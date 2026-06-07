"""Abstract base class for flight search providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

ProviderTier = Literal["official", "commercial", "affiliate", "experimental"]
ProviderRecommendation = Literal["recommended", "optional", "discouraged"]


@dataclass(frozen=True)
class ProviderMetadata:
    """Open-source suitability and setup notes for a flight provider."""

    display_name: str
    tier: ProviderTier
    is_official: bool
    recommendation: ProviderRecommendation
    credentials: tuple[str, ...]
    setup_difficulty: str
    docs_url: str
    supports_booking_links: bool = False
    supports_production: bool = True
    notes: str = ""


@dataclass
class FlightResult:
    """Standardized flight search result across all providers."""

    price: float
    currency: str
    airline: str
    origin: str
    destination: str
    outbound_date: date
    return_date: Optional[date]
    stopovers: int
    duration_minutes: int
    source: str  # "kiwi", "amadeus", etc.
    booking_link: str = ""
    flight_details: dict = field(default_factory=dict)

    @property
    def duration_display(self) -> str:
        """Human-readable duration like '5h 30m'."""
        h, m = divmod(self.duration_minutes, 60)
        return f"{h}h {m:02d}m"


class FlightProvider(ABC):
    """Base class that all flight providers must implement."""

    name: str = "base"
    metadata = ProviderMetadata(
        display_name="Base provider",
        tier="experimental",
        is_official=False,
        recommendation="discouraged",
        credentials=(),
        setup_difficulty="n/a",
        docs_url="",
        supports_production=False,
        notes="Abstract provider base class.",
    )

    @abstractmethod
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
        """Search for flights and return standardized results."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (e.g. aiohttp sessions)."""
        ...
