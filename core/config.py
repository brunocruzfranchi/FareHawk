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
    rapidapi_key: str = field(
        default_factory=lambda: os.getenv("RAPIDAPI_KEY", "")
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

    def validate(self) -> None:
        """Raise if critical config is missing."""
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not self.kiwi_api_key and not self.amadeus_api_key and not self.serpapi_key and not self.rapidapi_key:
            raise ValueError(
                "At least one flight provider is required. "
                "Set KIWI_API_KEY, AMADEUS_API_KEY/AMADEUS_API_SECRET, SERPAPI_KEY, or RAPIDAPI_KEY in .env"
            )


config = Config()
