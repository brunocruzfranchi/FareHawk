"""Multi-provider aggregation — query all active providers and merge results."""

import asyncio
import logging
from datetime import date
from typing import Optional

from providers.base import FlightProvider, FlightResult
from providers.kiwi import KiwiProvider
from providers.amadeus import AmadeusProvider
from providers.serpapi import SerpAPIProvider
from core.config import config

logger = logging.getLogger(__name__)


class FlightAggregator:
    """Query configured providers and return results sorted by price."""

    def __init__(self, providers: Optional[list[FlightProvider]] = None) -> None:
        self._providers: list[FlightProvider] = []
        if providers is not None:
            self._providers = providers
            return
        if config.serpapi_key:
            self._providers.append(SerpAPIProvider())
        if config.kiwi_api_key:
            self._providers.append(KiwiProvider())
        if config.amadeus_api_key and config.amadeus_api_secret:
            self._providers.append(AmadeusProvider())

        if not self._providers:
            logger.warning(
                "No flight providers configured — set SERPAPI_KEY, KIWI_API_KEY, "
                "AMADEUS_API_KEY/AMADEUS_API_SECRET in .env"
            )

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
        limit: int = 5,
        flight_type: str = "round",
        return_date_from: Optional[date] = None,
        return_date_to: Optional[date] = None,
    ) -> list[FlightResult]:
        """Search all providers concurrently and return merged results sorted by price."""
        tasks = [
            provider.search(
                origin, destination, date_from, date_to,
                currency=currency,
                direct_only=direct_only,
                max_stopovers=max_stopovers,
                limit=limit,
                flight_type=flight_type,
                return_date_from=return_date_from,
                return_date_to=return_date_to,
            )
            for provider in self._providers
        ]

        all_results: list[FlightResult] = []
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Provider %s failed: %s", self._providers[i].name, result)
            else:
                all_results.extend(result)

        # Sort by price ascending, then deduplicate equivalent itineraries while
        # keeping the cheapest source for each route/date/airline/stop profile.
        all_results.sort(key=lambda r: r.price)
        return self._deduplicate(all_results)[:limit]

    @staticmethod
    def _dedupe_key(result: FlightResult) -> tuple:
        """Identity key for equivalent itineraries from different providers."""
        return (
            result.origin.upper(),
            result.destination.upper(),
            result.outbound_date,
            result.return_date,
            result.airline.lower(),
            result.stopovers,
            result.duration_minutes,
        )

    @classmethod
    def _deduplicate(cls, results: list[FlightResult]) -> list[FlightResult]:
        seen: set[tuple] = set()
        unique: list[FlightResult] = []
        for result in results:
            key = cls._dedupe_key(result)
            if key in seen:
                continue
            seen.add(key)
            unique.append(result)
        return unique

    def provider_status(self) -> dict[str, dict]:
        """Return configured provider metadata for status/debug output."""
        return {
            provider.name: {
                "display_name": provider.metadata.display_name,
                "tier": provider.metadata.tier,
                "is_official": provider.metadata.is_official,
                "recommendation": provider.metadata.recommendation,
                "credentials": list(provider.metadata.credentials),
                "setup_difficulty": provider.metadata.setup_difficulty,
                "docs_url": provider.metadata.docs_url,
                "supports_booking_links": provider.metadata.supports_booking_links,
                "supports_production": provider.metadata.supports_production,
                "notes": provider.metadata.notes,
            }
            for provider in self._providers
        }

    async def close(self) -> None:
        """Close all provider sessions."""
        for p in self._providers:
            try:
                await p.close()
            except Exception:
                logger.exception("Error closing provider %s", p.name)
