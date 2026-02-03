"""Amadeus flight search provider — Phase 2 stub."""

import logging
from datetime import date
from typing import Optional

from providers.base import FlightProvider, FlightResult

logger = logging.getLogger(__name__)


class AmadeusProvider(FlightProvider):
    """Amadeus API provider (Phase 2 — not yet implemented)."""

    name = "amadeus"

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
    ) -> list[FlightResult]:
        # TODO: Implement Amadeus Self-Service API integration in Phase 2
        logger.debug("Amadeus provider not yet implemented — skipping")
        return []

    async def close(self) -> None:
        pass
