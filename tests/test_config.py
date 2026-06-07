import pytest

from core.config import Config


def _config(**overrides) -> Config:
    values = {
        "telegram_bot_token": "telegram-token",
        "kiwi_api_key": "",
        "amadeus_api_key": "",
        "amadeus_api_secret": "",
        "serpapi_key": "",
    }
    values.update(overrides)
    return Config(**values)


def test_config_requires_at_least_one_provider():
    with pytest.raises(ValueError, match="At least one flight provider"):
        _config().validate()


def test_config_requires_complete_amadeus_credentials():
    with pytest.raises(ValueError, match="must be set together"):
        _config(amadeus_api_key="key").validate()

    with pytest.raises(ValueError, match="must be set together"):
        _config(amadeus_api_secret="secret").validate()


def test_config_accepts_supported_provider_credentials():
    _config(kiwi_api_key="key").validate()
    _config(serpapi_key="key").validate()
    _config(amadeus_api_key="key", amadeus_api_secret="secret").validate()
