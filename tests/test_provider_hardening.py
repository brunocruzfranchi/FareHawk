import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

import providers.aggregator as aggregator_module
from core.config import Config
from providers.aggregator import FlightAggregator
from providers.amadeus import AmadeusProvider
from providers.base import FlightProvider, FlightResult, ProviderMetadata
from providers.kiwi import KiwiProvider
from providers.serpapi import SerpAPIProvider


class _StaticProvider(FlightProvider):
    def __init__(self, name: str, results: list[FlightResult]):
        self.name = name
        self._results = results

    async def search(self, *args, **kwargs) -> list[FlightResult]:
        return self._results

    async def close(self) -> None:
        return None


def _result(price: float, *, source: str, booking_link: str = "") -> FlightResult:
    return FlightResult(
        price=price,
        currency="USD",
        airline="Test Air",
        origin="JFK",
        destination="BCN",
        outbound_date=date(2026, 10, 17),
        return_date=date(2026, 11, 1),
        stopovers=0,
        duration_minutes=480,
        source=source,
        booking_link=booking_link,
    )


def test_provider_metadata_classifies_setup_risk_and_official_status():
    assert isinstance(AmadeusProvider.metadata, ProviderMetadata)
    assert AmadeusProvider.metadata.tier == "official"
    assert AmadeusProvider.metadata.is_official is True
    assert AmadeusProvider.metadata.recommendation == "recommended"

    assert SerpAPIProvider.metadata.tier == "commercial"
    assert SerpAPIProvider.metadata.is_official is False
    assert SerpAPIProvider.metadata.recommendation == "optional"

    assert KiwiProvider.metadata.tier == "affiliate"
    assert KiwiProvider.metadata.recommendation == "optional"


def test_removed_rapidapi_skyscanner_is_not_a_supported_provider():
    supported = Config(telegram_bot_token="telegram", amadeus_api_key="key", amadeus_api_secret="secret").provider_status()

    assert "rapidapi_skyscanner" not in supported


def test_amadeus_environment_selects_test_or_production_urls():
    test_config = Config(
        telegram_bot_token="telegram",
        amadeus_api_key="key",
        amadeus_api_secret="secret",
        amadeus_env="test",
    )
    prod_config = Config(
        telegram_bot_token="telegram",
        amadeus_api_key="key",
        amadeus_api_secret="secret",
        amadeus_env="production",
    )

    test_provider = AmadeusProvider(config_override=test_config)
    prod_provider = AmadeusProvider(config_override=prod_config)

    assert test_provider.auth_url.startswith("https://test.api.amadeus.com/")
    assert test_provider.search_url.startswith("https://test.api.amadeus.com/")
    assert prod_provider.auth_url.startswith("https://api.amadeus.com/")
    assert prod_provider.search_url.startswith("https://api.amadeus.com/")


def test_amadeus_environment_rejects_unknown_values():
    with pytest.raises(ValueError, match="AMADEUS_ENV"):
        Config(
            telegram_bot_token="telegram",
            amadeus_api_key="key",
            amadeus_api_secret="secret",
            amadeus_env="sandbox",
        ).validate()


def test_aggregator_deduplicates_equivalent_itineraries_by_lowest_price():
    duplicate_a = _result(500, source="amadeus", booking_link="https://a.example")
    duplicate_b = _result(450, source="serpapi", booking_link="https://b.example")
    distinct = _result(550, source="kiwi", booking_link="https://c.example")
    distinct.airline = "Other Air"

    aggregator = FlightAggregator(providers=[
        _StaticProvider("amadeus", [duplicate_a]),
        _StaticProvider("serpapi", [duplicate_b, distinct]),
    ])

    results = asyncio.run(aggregator.search(
        "JFK",
        "BCN",
        date(2026, 10, 17),
        date(2026, 11, 1),
        limit=10,
    ))

    assert results == [duplicate_b, distinct]


def test_aggregator_provider_status_includes_metadata(monkeypatch):
    monkeypatch.setattr(
        aggregator_module,
        "config",
        SimpleNamespace(
            serpapi_key="serpapi",
            kiwi_api_key="kiwi",
            amadeus_api_key="amadeus",
            amadeus_api_secret="secret",
        ),
    )

    aggregator = FlightAggregator()
    status = aggregator.provider_status()

    assert status["amadeus"]["tier"] == "official"
    assert status["serpapi"]["tier"] == "commercial"
    assert status["kiwi"]["tier"] == "affiliate"
    assert "rapidapi_skyscanner" not in status


def test_kiwi_round_trip_return_date_is_parsed_from_return_segment():
    provider = KiwiProvider()
    data = {
        "data": [
            {
                "price": 321,
                "dTime": 1792195200,
                "local_departure": "2026-10-17T08:00:00.000Z",
                "duration": {"departure": 28800, "return": 30000},
                "deep_link": "https://kiwi.example/booking",
                "route": [
                    {"airline": "AA", "return": 0, "local_departure": "2026-10-17T08:00:00.000Z"},
                    {"airline": "AA", "return": 1, "local_departure": "2026-11-01T10:00:00.000Z"},
                ],
            }
        ]
    }

    results = provider._parse_results(data, "JFK", "BCN", "USD")

    assert len(results) == 1
    assert results[0].return_date == date(2026, 11, 1)
