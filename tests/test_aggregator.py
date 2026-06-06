from types import SimpleNamespace

import providers.aggregator as aggregator_module
from providers.aggregator import FlightAggregator


def _provider_config(**overrides):
    values = {
        "kiwi_api_key": "",
        "amadeus_api_key": "",
        "amadeus_api_secret": "",
        "serpapi_key": "",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_aggregator_enables_all_configured_providers(monkeypatch):
    monkeypatch.setattr(
        aggregator_module,
        "config",
        _provider_config(
            serpapi_key="serpapi",
            kiwi_api_key="kiwi",
            amadeus_api_key="amadeus",
            amadeus_api_secret="secret",
        ),
    )

    aggregator = FlightAggregator()

    assert [provider.name for provider in aggregator._providers] == [
        "serpapi",
        "kiwi",
        "amadeus",
    ]


def test_aggregator_skips_incomplete_amadeus_credentials(monkeypatch):
    monkeypatch.setattr(
        aggregator_module,
        "config",
        _provider_config(amadeus_api_key="amadeus"),
    )

    aggregator = FlightAggregator()

    assert [provider.name for provider in aggregator._providers] == []
