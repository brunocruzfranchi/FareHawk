"""Amadeus Self-Service flight search provider.

Uses the Flight Offers Search API v2:
  - Auth: OAuth2 client_credentials grant → access_token
  - Search: GET /v2/shopping/flight-offers
  - Docs: https://developers.amadeus.com/self-service/category/flights/api-doc/flight-offers-search
"""

import logging
import time
from datetime import date, datetime, timedelta
from typing import Optional

import aiohttp
from urllib.parse import quote

from core.config import config
from providers.base import FlightProvider, FlightResult

logger = logging.getLogger(__name__)

AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


class AmadeusProvider(FlightProvider):
    """Search flights via the Amadeus Self-Service API."""

    name = "amadeus"

    def __init__(self) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _ensure_token(self) -> str:
        """Obtain or refresh OAuth2 access token."""
        # Return cached token if still valid (with 60s buffer)
        if self._access_token and time.time() < (self._token_expires_at - 60):
            return self._access_token

        session = await self._get_session()

        data = {
            "grant_type": "client_credentials",
            "client_id": config.amadeus_api_key,
            "client_secret": config.amadeus_api_secret,
        }

        try:
            async with session.post(
                AUTH_URL,
                data=data,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.error("Amadeus auth failed %d: %s", resp.status, body[:500])
                    raise RuntimeError(f"Amadeus auth failed: {resp.status}")

                result = await resp.json()
                self._access_token = result["access_token"]
                self._token_expires_at = time.time() + result.get("expires_in", 1799)
                logger.info("Amadeus token obtained (expires in %ds)", result.get("expires_in", 0))
                return self._access_token

        except aiohttp.ClientError:
            logger.exception("Amadeus auth request failed")
            raise

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
        """Search Amadeus Flight Offers.

        Since Amadeus requires a specific departure date (not a range),
        we search multiple dates across the range (sampling up to 5 dates
        to stay within free tier limits).
        """
        if not config.amadeus_api_key or not config.amadeus_api_secret:
            logger.debug("Amadeus not configured — skipping")
            return []

        token = await self._ensure_token()
        session = await self._get_session()

        # Sample outbound dates across the range (max 5 to conserve API calls)
        total_days = (date_to - date_from).days
        if flight_type == "round" and not return_date_from and total_days > 7:
            # Range spans the whole trip — only sample outbound from first portion
            flex = min(3, total_days // 4)
            sample_dates = [
                date_from,
                date_from + timedelta(days=flex),
                date_from + timedelta(days=flex * 2),
            ]
        elif total_days <= 0:
            sample_dates = [date_from]
        elif total_days <= 4:
            sample_dates = [date_from + timedelta(days=i) for i in range(total_days + 1)]
        else:
            step = total_days / 4
            sample_dates = [date_from + timedelta(days=int(i * step)) for i in range(5)]

        # Determine return date for round trips
        return_date_sample: Optional[date] = None
        if flight_type == "round":
            if return_date_from and return_date_to:
                ret_days = (return_date_to - return_date_from).days
                return_date_sample = return_date_from + timedelta(days=ret_days // 2)
            elif return_date_from:
                return_date_sample = return_date_from

        all_results: list[FlightResult] = []

        for dep_date in sample_dates:
            try:
                # For round trip, calculate a proportional return date if we have a range
                ret_date = return_date_sample
                if flight_type == "round" and ret_date is None:
                    # No return dates set — if outbound range > 7 days, assume date_to is return
                    if (date_to - date_from).days > 7:
                        ret_date = date_to
                    else:
                        ret_date = dep_date + timedelta(days=14)

                results = await self._search_date(
                    session, token, origin, destination, dep_date,
                    currency=currency,
                    direct_only=direct_only,
                    max_stopovers=max_stopovers,
                    adults=adults,
                    limit=limit,
                    return_date=ret_date if flight_type == "round" else None,
                )
                all_results.extend(results)
            except Exception:
                logger.exception("Amadeus search failed for date %s", dep_date)
                continue

        # Sort by price and limit
        all_results.sort(key=lambda r: r.price)
        return all_results[:limit]

    async def _search_date(
        self,
        session: aiohttp.ClientSession,
        token: str,
        origin: str,
        destination: str,
        departure_date: date,
        *,
        currency: str = "USD",
        direct_only: bool = False,
        max_stopovers: Optional[int] = None,
        adults: int = 1,
        limit: int = 5,
        return_date: Optional[date] = None,
    ) -> list[FlightResult]:
        """Search for a specific departure date."""
        params: dict = {
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date.isoformat(),
            "adults": adults,
            "currencyCode": currency,
            "max": min(limit, 10),  # Amadeus max per request
        }

        if return_date:
            params["returnDate"] = return_date.isoformat()

        if direct_only:
            params["nonStop"] = "true"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        logger.info(
            "Amadeus search: %s → %s on %s",
            origin, destination, departure_date,
        )

        try:
            async with session.get(
                SEARCH_URL,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status == 401:
                    # Token expired, refresh and retry once
                    logger.warning("Amadeus token expired, refreshing...")
                    self._access_token = None
                    token = await self._ensure_token()
                    headers["Authorization"] = f"Bearer {token}"
                    async with session.get(
                        SEARCH_URL, params=params, headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as retry_resp:
                        if retry_resp.status != 200:
                            body = await retry_resp.text()
                            logger.error("Amadeus retry failed %d: %s", retry_resp.status, body[:500])
                            return []
                        data = await retry_resp.json()

                elif resp.status != 200:
                    body = await resp.text()
                    logger.error("Amadeus API error %d: %s", resp.status, body[:500])
                    return []
                else:
                    data = await resp.json()

        except aiohttp.ClientError:
            logger.exception("Amadeus API request failed")
            return []

        return self._parse_results(data, origin, destination, currency)

    def _parse_results(
        self,
        data: dict,
        origin: str,
        destination: str,
        currency: str,
    ) -> list[FlightResult]:
        """Parse Amadeus flight-offers response into FlightResult list."""
        results: list[FlightResult] = []
        offers = data.get("data", [])
        dictionaries = data.get("dictionaries", {})
        carriers = dictionaries.get("carriers", {})

        for offer in offers:
            try:
                price = float(offer.get("price", {}).get("grandTotal", 0))
                if price <= 0:
                    continue

                itineraries = offer.get("itineraries", [])
                if not itineraries:
                    continue

                # Outbound itinerary
                outbound_itin = itineraries[0]
                segments = outbound_itin.get("segments", [])
                if not segments:
                    continue

                # Airlines
                airline_codes = {seg.get("carrierCode", "??") for seg in segments}
                airline_names = [carriers.get(code, code) for code in sorted(airline_codes)]

                # Departure date
                dep_str = segments[0].get("departure", {}).get("at", "")
                outbound_date = None
                if dep_str:
                    try:
                        outbound_date = datetime.fromisoformat(dep_str).date()
                    except ValueError:
                        outbound_date = datetime.strptime(dep_str[:10], "%Y-%m-%d").date()

                # Return date (if round trip)
                return_date = None
                if len(itineraries) > 1:
                    ret_segments = itineraries[1].get("segments", [])
                    if ret_segments:
                        ret_dep = ret_segments[0].get("departure", {}).get("at", "")
                        if ret_dep:
                            try:
                                return_date = datetime.fromisoformat(ret_dep).date()
                            except ValueError:
                                return_date = datetime.strptime(ret_dep[:10], "%Y-%m-%d").date()

                # Duration — parse ISO 8601 duration (e.g., "PT12H30M")
                duration_str = outbound_itin.get("duration", "")
                duration_minutes = self._parse_duration(duration_str)

                # Stopovers = segments - 1
                stopovers = max(len(segments) - 1, 0)

                # Check max_stopovers filter
                # (Amadeus nonStop param handles direct, but for multi-stop filtering)

                # Build fallback booking link (Google Flights)
                booking_link = self._build_booking_link_fallback(
                    origin, destination, outbound_date, return_date,
                )

                results.append(FlightResult(
                    price=price,
                    currency=currency,
                    airline=", ".join(airline_names),
                    origin=origin.upper(),
                    destination=destination.upper(),
                    outbound_date=outbound_date,
                    return_date=return_date,
                    stopovers=stopovers,
                    duration_minutes=duration_minutes,
                    source=self.name,
                    booking_link=booking_link,
                    flight_details={
                        "offer_id": offer.get("id"),
                        "validating_airline": offer.get("validatingAirlineCodes", []),
                        "cabin": self._extract_cabin(offer),
                        "segments": len(segments),
                    },
                ))

            except Exception:
                logger.exception("Failed to parse Amadeus offer")
                continue

        logger.info("Amadeus returned %d results for %s→%s", len(results), origin, destination)
        return results

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Parse ISO 8601 duration (e.g., 'PT12H30M') into total minutes."""
        if not duration_str:
            return 0

        total = 0
        duration_str = duration_str.replace("PT", "")

        if "H" in duration_str:
            parts = duration_str.split("H")
            try:
                total += int(parts[0]) * 60
            except ValueError:
                pass
            duration_str = parts[1] if len(parts) > 1 else ""

        if "M" in duration_str:
            try:
                total += int(duration_str.replace("M", ""))
            except ValueError:
                pass

        return total

    @staticmethod
    def _build_booking_link_fallback(
        origin: str, destination: str, outbound_date=None, return_date=None,
    ) -> str:
        """Build a Google Flights fallback URL."""
        q = f"Flights from {origin} to {destination}"
        if outbound_date:
            q += f" on {outbound_date.isoformat()}"
        if return_date:
            q += f" return {return_date.isoformat()}"
        return f"https://www.google.com/travel/flights?q={quote(q)}"

    @staticmethod
    def _extract_cabin(offer: dict) -> str:
        """Extract cabin class from first segment."""
        try:
            return (
                offer.get("travelerPricings", [{}])[0]
                .get("fareDetailsBySegment", [{}])[0]
                .get("cabin", "ECONOMY")
            )
        except (IndexError, KeyError):
            return "ECONOMY"

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
