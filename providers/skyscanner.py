"""Skyscanner flight search provider via RapidAPI.

Uses the Sky-Scanner3 API on RapidAPI:
  - Roundtrip: GET /flights/search-roundtrip
  - One-way:   GET /flights/search-one-way
  - Host: sky-scanner3.p.rapidapi.com
"""

import logging
from datetime import date, timedelta
from typing import Optional

import aiohttp

from core.config import config
from providers.base import FlightProvider, FlightResult

logger = logging.getLogger(__name__)

BASE_URL = "https://sky-scanner3.p.rapidapi.com/flights"


class SkyscannerProvider(FlightProvider):
    """Search flights via Skyscanner (RapidAPI)."""

    name = "skyscanner"

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _headers(self) -> dict:
        return {
            "X-RapidAPI-Key": config.rapidapi_key,
            "X-RapidAPI-Host": "sky-scanner3.p.rapidapi.com",
        }

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
        """Search Skyscanner via RapidAPI."""
        if not config.rapidapi_key:
            logger.debug("RapidAPI key not configured — skipping Skyscanner")
            return []

        session = await self._get_session()

        # Sample up to 3 outbound dates across the range
        total_days = (date_to - date_from).days
        if flight_type == "round" and not return_date_from and total_days > 7:
            flex = min(3, total_days // 4)
            sample_dates = [
                date_from,
                date_from + timedelta(days=flex),
                date_from + timedelta(days=flex * 2),
            ]
        elif total_days <= 0:
            sample_dates = [date_from]
        elif total_days <= 2:
            sample_dates = [date_from + timedelta(days=i) for i in range(total_days + 1)]
        else:
            step = total_days / 2
            sample_dates = [
                date_from,
                date_from + timedelta(days=int(step)),
                date_to,
            ]

        # Determine return date
        return_sample: Optional[date] = None
        if flight_type == "round":
            if return_date_from and return_date_to:
                ret_days = (return_date_to - return_date_from).days
                return_sample = return_date_from + timedelta(days=ret_days // 2)
            elif return_date_from:
                return_sample = return_date_from

        all_results: list[FlightResult] = []

        for dep_date in sample_dates:
            try:
                ret_date = return_sample
                if flight_type == "round" and ret_date is None:
                    if (date_to - date_from).days > 7:
                        ret_date = date_to
                    else:
                        ret_date = dep_date + timedelta(days=14)

                results = await self._search_date(
                    session, origin, destination, dep_date,
                    return_date=ret_date if flight_type == "round" else None,
                    currency=currency,
                    adults=adults,
                    limit=limit,
                )
                all_results.extend(results)
            except Exception:
                logger.exception("Skyscanner search failed for date %s", dep_date)
                continue

        all_results.sort(key=lambda r: r.price)
        return all_results[:limit]

    async def _search_date(
        self,
        session: aiohttp.ClientSession,
        origin: str,
        destination: str,
        departure_date: date,
        *,
        return_date: Optional[date] = None,
        currency: str = "USD",
        adults: int = 1,
        limit: int = 5,
    ) -> list[FlightResult]:
        """Search for a specific departure date."""
        params: dict = {
            "fromEntityId": origin.upper(),
            "toEntityId": destination.upper(),
            "departDate": departure_date.isoformat(),
            "currency": currency,
            "adults": str(adults),
        }

        if return_date:
            params["returnDate"] = return_date.isoformat()
            url = f"{BASE_URL}/search-roundtrip"
        else:
            url = f"{BASE_URL}/search-one-way"

        logger.info(
            "Skyscanner search: %s → %s on %s (return=%s)",
            origin, destination, departure_date, return_date,
        )

        try:
            async with session.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Skyscanner API error %d: %s", resp.status, body[:500])
                    return []
                data = await resp.json()
        except aiohttp.ClientError:
            logger.exception("Skyscanner API request failed")
            return []

        return self._parse_results(data, origin, destination, currency, departure_date, return_date)

    def _parse_results(
        self,
        data: dict,
        origin: str,
        destination: str,
        currency: str,
        departure_date: date,
        return_date: Optional[date],
    ) -> list[FlightResult]:
        """Parse Skyscanner RapidAPI response into FlightResult list."""
        results: list[FlightResult] = []

        # Response structure: data.itineraries[]
        itineraries = data.get("data", {}).get("itineraries", [])

        for itin in itineraries:
            try:
                # Price
                price_raw = itin.get("price", {}).get("raw")
                if not price_raw or price_raw <= 0:
                    continue
                price = float(price_raw)

                # Legs
                legs = itin.get("legs", [])
                if not legs:
                    continue

                outbound_leg = legs[0]

                # Airlines from carriers
                carriers = outbound_leg.get("carriers", {}).get("marketing", [])
                airline_names = [c.get("name", "?") for c in carriers]

                # Stopovers
                stop_count = outbound_leg.get("stopCount", 0)

                # Duration in minutes
                duration_minutes = outbound_leg.get("durationInMinutes", 0)

                # Outbound date from leg departure
                dep_str = outbound_leg.get("departure", "")
                outbound_date = departure_date
                if dep_str and len(dep_str) >= 10:
                    try:
                        from datetime import datetime
                        outbound_date = datetime.fromisoformat(dep_str[:10]).date()
                    except (ValueError, TypeError):
                        pass

                # Return date from second leg if present
                ret_date = return_date
                if len(legs) > 1:
                    ret_dep = legs[1].get("departure", "")
                    if ret_dep and len(ret_dep) >= 10:
                        try:
                            from datetime import datetime
                            ret_date = datetime.fromisoformat(ret_dep[:10]).date()
                        except (ValueError, TypeError):
                            pass

                # Booking link — prefer deep link from response
                deep_links = itin.get("deepLinks", [])
                if deep_links:
                    booking_link = deep_links[0].get("link", "") or deep_links[0].get("url", "")
                else:
                    booking_link = (
                        f"https://www.skyscanner.com/transport/flights/"
                        f"{origin.lower()}/{destination.lower()}/"
                        f"{departure_date.strftime('%y%m%d')}/"
                    )
                    if return_date:
                        booking_link += f"{return_date.strftime('%y%m%d')}/"

                results.append(FlightResult(
                    price=price,
                    currency=currency,
                    airline=", ".join(airline_names) if airline_names else "Unknown",
                    origin=origin.upper(),
                    destination=destination.upper(),
                    outbound_date=outbound_date,
                    return_date=ret_date,
                    stopovers=stop_count,
                    duration_minutes=duration_minutes,
                    source=self.name,
                    booking_link=booking_link,
                    flight_details={
                        "legs": len(legs),
                        "score": itin.get("score", 0),
                        "tags": itin.get("tags", []),
                    },
                ))

            except Exception:
                logger.exception("Failed to parse Skyscanner itinerary")
                continue

        logger.info("Skyscanner returned %d results for %s→%s", len(results), origin, destination)
        return results

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
