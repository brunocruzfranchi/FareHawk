"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Immutable application configuration."""

    # Telegram
    telegram_bot_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )

    # Flight API keys
    kiwi_api_key: str = field(
        default_factory=lambda: os.getenv("KIWI_API_KEY", "")
    )
    amadeus_api_key: str = field(
        default_factory=lambda: os.getenv("AMADEUS_API_KEY", "")
    )
    amadeus_api_secret: str = field(
        default_factory=lambda: os.getenv("AMADEUS_API_SECRET", "")
    )
    serpapi_key: str = field(
        default_factory=lambda: os.getenv("SERPAPI_KEY", "")
    )
    amadeus_env: str = field(
        default_factory=lambda: os.getenv("AMADEUS_ENV", "test")
    )

    # Database
    database_url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///data/farehawk.db")
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    # Defaults
    default_check_interval_hours: int = 3
    default_language: str = "en"
    default_currency: str = "USD"
    price_drop_threshold_pct: float = 10.0  # Alert when price drops >10%

    def provider_status(self) -> dict[str, bool]:
        """Return enabled provider flags based on complete credentials."""
        return {
            "kiwi": bool(self.kiwi_api_key),
            "amadeus": bool(self.amadeus_api_key and self.amadeus_api_secret),
            "serpapi": bool(self.serpapi_key),
        }

    def validate(self) -> None:
        """Raise if critical config is missing."""
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if bool(self.amadeus_api_key) != bool(self.amadeus_api_secret):
            raise ValueError("AMADEUS_API_KEY and AMADEUS_API_SECRET must be set together")
        if self.amadeus_env not in {"test", "production"}:
            raise ValueError("AMADEUS_ENV must be either 'test' or 'production'")
        if not any(self.provider_status().values()):
            raise ValueError(
                "At least one flight provider is required. "
                "Set KIWI_API_KEY, AMADEUS_API_KEY/AMADEUS_API_SECRET, or SERPAPI_KEY in .env"
            )


config = Config()
