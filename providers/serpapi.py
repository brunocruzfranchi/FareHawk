"""SerpAPI Google Flights provider.

Uses the SerpAPI Google Flights engine:
  - Endpoint: https://serpapi.com/search.json
  - Docs: https://serpapi.com/google-flights-api
"""

import logging
from datetime import date, timedelta
from typing import Optional
from urllib.parse import quote

import aiohttp

from core.config import config
from providers.base import FlightProvider, FlightResult

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search.json"


class SerpAPIProvider(FlightProvider):
    """Search flights via SerpAPI Google Flights."""

    name = "serpapi"

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
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
        """Search SerpAPI Google Flights.

        Since SerpAPI needs specific dates, we sample up to 3 dates
        across the range to conserve the free tier (100 calls/month).
        """
        if not config.serpapi_key:
            logger.debug("SerpAPI not configured — skipping")
            return []

        session = await self._get_session()

        # Sample up to 3 outbound dates
        # If return dates aren't set and range is > 7 days, the range likely
        # spans the whole trip (outbound to return), so only sample the first few days
        total_days = (date_to - date_from).days
        if flight_type == "round" and not return_date_from and total_days > 7:
            # Range is the whole trip — sample outbound from first ~3 days
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

        # Determine return date for round trips
        return_sample: Optional[date] = None
        if flight_type == "round" and return_date_from and return_date_to:
            ret_days = (return_date_to - return_date_from).days
            return_sample = return_date_from + timedelta(days=ret_days // 2)
        elif flight_type == "round" and return_date_from:
            return_sample = return_date_from

        all_results: list[FlightResult] = []

        for dep_date in sample_dates:
            try:
                ret_date = return_sample
                if flight_type == "round" and ret_date is None:
                    # No return dates set — estimate: use date_to + 14 days from dep
                    # or if date range is > 7 days, assume date_to is roughly the return
                    if (date_to - date_from).days > 7:
                        ret_date = date_to
                    else:
                        ret_date = dep_date + timedelta(days=14)

                results = await self._search_date(
                    session, origin, destination, dep_date,
                    return_date=ret_date if flight_type == "round" else None,
                    currency=currency,
                    direct_only=direct_only,
                    flight_type=flight_type,
                    adults=adults,
                    limit=limit,
                )
                all_results.extend(results)
            except Exception:
                logger.exception("SerpAPI search failed for date %s", dep_date)
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
        direct_only: bool = False,
        flight_type: str = "round",
        adults: int = 1,
        limit: int = 5,
    ) -> list[FlightResult]:
        """Search for a specific departure date."""
        params: dict = {
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": departure_date.isoformat(),
            "currency": currency,
            "type": "1" if flight_type == "round" else "2",
            "api_key": config.serpapi_key,
            "adults": adults,
        }

        if return_date and flight_type == "round":
            params["return_date"] = return_date.isoformat()

        if direct_only:
            params["stops"] = "0"

        logger.info(
            "SerpAPI search: %s → %s on %s (type=%s)",
            origin, destination, departure_date, flight_type,
        )

        try:
            async with session.get(
                SERPAPI_URL,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("SerpAPI error %d: %s", resp.status, body[:500])
                    return []
                data = await resp.json()
        except aiohttp.ClientError:
            logger.exception("SerpAPI request failed")
            return []

        return self._parse_results(
            data, origin, destination, currency,
            departure_date, return_date,
        )

    def _parse_results(
        self,
        data: dict,
        origin: str,
        destination: str,
        currency: str,
        departure_date: date,
        return_date: Optional[date],
    ) -> list[FlightResult]:
        """Parse SerpAPI Google Flights response into FlightResult list."""
        results: list[FlightResult] = []

        # Combine best_flights and other_flights
        flights = data.get("best_flights", []) + data.get("other_flights", [])

        for flight in flights:
            try:
                price = flight.get("price")
                if not price or price <= 0:
                    continue

                legs = flight.get("flights", [])
                if not legs:
                    continue

                # Total duration in minutes
                total_duration = flight.get("total_duration", 0)

                # Airlines from legs
                airlines = list({leg.get("airline", "?") for leg in legs})

                # Stopovers = layovers count
                layovers = flight.get("layovers", [])
                stopovers = len(layovers)

                # Parse outbound date from first leg
                first_leg = legs[0]
                dep_info = first_leg.get("departure_airport", {})
                outbound_date = departure_date
                dep_time = dep_info.get("time", "")
                if dep_time and len(dep_time) >= 10:
                    try:
                        from datetime import datetime
                        outbound_date = datetime.fromisoformat(dep_time[:10]).date()
                    except (ValueError, TypeError):
                        pass

                # Build Google Flights deep link as booking link
                booking_link = self._build_google_flights_link(
                    origin, destination, departure_date, return_date,
                )

                # Flight details
                flight_details = {
                    "legs": [],
                    "carbon_emissions": flight.get("carbon_emissions", {}),
                    "type": flight.get("type", ""),
                    "airline_logo": flight.get("airline_logo", ""),
                    "departure_token": flight.get("departure_token", ""),
                }

                for leg in legs:
                    flight_details["legs"].append({
                        "departure_airport": leg.get("departure_airport", {}),
                        "arrival_airport": leg.get("arrival_airport", {}),
                        "duration": leg.get("duration", 0),
                        "airplane": leg.get("airplane", ""),
                        "airline": leg.get("airline", ""),
                        "flight_number": leg.get("flight_number", ""),
                        "travel_class": leg.get("travel_class", ""),
                        "legroom": leg.get("legroom", ""),
                    })

                results.append(FlightResult(
                    price=float(price),
                    currency=currency,
                    airline=", ".join(sorted(airlines)),
                    origin=origin.upper(),
                    destination=destination.upper(),
                    outbound_date=outbound_date,
                    return_date=return_date,
                    stopovers=stopovers,
                    duration_minutes=total_duration,
                    source=self.name,
                    booking_link=booking_link,
                    flight_details=flight_details,
                ))

            except Exception:
                logger.exception("Failed to parse SerpAPI flight result")
                continue

        logger.info("SerpAPI returned %d results for %s→%s", len(results), origin, destination)
        return results

    @staticmethod
    def _build_google_flights_link(
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
    ) -> str:
        """Build a Google Flights URL for the given route."""
        q = f"Flights from {origin} to {destination} on {departure_date.isoformat()}"
        if return_date:
            q += f" return {return_date.isoformat()}"
        return f"https://www.google.com/travel/flights?q={quote(q)}"

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
