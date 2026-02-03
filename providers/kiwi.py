"""Kiwi / Tequila flight search provider."""

import logging
from datetime import date, datetime
from typing import Optional

import aiohttp

from core.config import config
from providers.base import FlightProvider, FlightResult

logger = logging.getLogger(__name__)

TEQUILA_BASE = "https://api.tequila.kiwi.com"


class KiwiProvider(FlightProvider):
    """Search flights via the Kiwi Tequila API."""

    name = "kiwi"

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"apikey": config.kiwi_api_key}
            )
        return self._session

    async def search(
        self,
        origin: str,
        destination: str,
        date_from: date,
        date_to: date,
        *,
        currency: str = "USD",
        direct_only: bool = False,
        max_stopovers: Optional[int] = None,
        adults: int = 1,
        limit: int = 5,
        flight_type: str = "round",
        return_date_from: Optional[date] = None,
        return_date_to: Optional[date] = None,
    ) -> list[FlightResult]:
        session = await self._get_session()

        params: dict = {
            "fly_from": origin,
            "fly_to": destination,
            "date_from": date_from.strftime("%d/%m/%Y"),
            "date_to": date_to.strftime("%d/%m/%Y"),
            "curr": currency,
            "adults": adults,
            "limit": limit,
            "sort": "price",
            "flight_type": flight_type,
        }

        if flight_type == "round" and return_date_from:
            params["return_from"] = return_date_from.strftime("%d/%m/%Y")
        if flight_type == "round" and return_date_to:
            params["return_to"] = return_date_to.strftime("%d/%m/%Y")

        if direct_only:
            params["direct_flights_only"] = True
        if max_stopovers is not None:
            params["max_stopovers"] = max_stopovers

        url = f"{TEQUILA_BASE}/v2/search"
        logger.info("Kiwi search: %s → %s  (%s – %s)", origin, destination, date_from, date_to)

        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Kiwi API error %d: %s", resp.status, body[:500])
                    return []
                data = await resp.json()
        except Exception:
            logger.exception("Kiwi API request failed")
            return []

        results: list[FlightResult] = []
        for item in data.get("data", []):
            try:
                airlines = {r.get("airline", "?") for r in item.get("route", [])}
                outbound = datetime.strptime(item["dTime"][:10] if isinstance(item.get("dTime"), str)
                                              else datetime.utcfromtimestamp(item["dTime"]).strftime("%Y-%m-%d"),
                                              "%Y-%m-%d").date()
                return_dt = None
                if item.get("return"):
                    # Kiwi provides route segments; last segment's arrival is the return
                    pass  # return_date parsed below

                # Parse outbound/return from local_departure
                local_dep = item.get("local_departure", "")
                local_arr = item.get("local_arrival", "")

                try:
                    outbound = datetime.fromisoformat(local_dep[:10]).date()
                except Exception:
                    pass

                # Duration
                duration = item.get("duration", {})
                total_sec = (duration.get("departure", 0) or 0) + (duration.get("return", 0) or 0)
                total_min = total_sec // 60 if total_sec else item.get("fly_duration", 0)

                # Stopovers: number of route segments minus 1 for outbound
                route = item.get("route", [])
                # Count outbound segments (those before the return flag)
                outbound_segments = sum(1 for r in route if r.get("return") == 0)
                stops = max(outbound_segments - 1, 0)

                # Build booking link
                booking_link = item.get("deep_link", "")

                results.append(FlightResult(
                    price=float(item["price"]),
                    currency=currency,
                    airline=", ".join(sorted(airlines)),
                    origin=origin.upper(),
                    destination=destination.upper(),
                    outbound_date=outbound,
                    return_date=return_dt,
                    stopovers=stops,
                    duration_minutes=total_min,
                    source=self.name,
                    booking_link=booking_link,
                    flight_details={
                        "id": item.get("id"),
                        "route_count": len(route),
                        "quality": item.get("quality"),
                    },
                ))
            except Exception:
                logger.exception("Failed to parse Kiwi result item")
                continue

        logger.info("Kiwi returned %d results for %s→%s", len(results), origin, destination)
        return results

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
