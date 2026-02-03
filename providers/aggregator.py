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
    """Query multiple providers and return sorted, de-duplicated results."""

    def __init__(self) -> None:
        self._providers: list[FlightProvider] = []
        # Always add Kiwi if key is available
        if config.kiwi_api_key:
            self._providers.append(KiwiProvider())
        # Amadeus
        if config.amadeus_api_key:
            self._providers.append(AmadeusProvider())
        # SerpAPI Google Flights
        if config.serpapi_key:
            self._providers.append(SerpAPIProvider())

        if not self._providers:
            logger.warning("No flight providers configured — set KIWI_API_KEY in .env")

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

        # Sort by price ascending
        all_results.sort(key=lambda r: r.price)

        # Limit total results
        return all_results[:limit]

    async def close(self) -> None:
        """Close all provider sessions."""
        for p in self._providers:
            try:
                await p.close()
            except Exception:
                logger.exception("Error closing provider %s", p.name)
