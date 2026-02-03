"""FareHawk Telegram Bot — Entry point."""

import asyncio
import logging
import sys
from functools import partial

from telegram.ext import Application

from core.config import config
from core.database import init_db
from core.scheduler import start_scheduler, stop_scheduler
from providers.aggregator import FlightAggregator
from services.price_checker import run_price_check

from bot.handlers import start, trips, search, settings

# ── Logging ───────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    stream=sys.stdout,
)
logger = logging.getLogger("farehawk")


def main() -> None:
    """Build and run the Telegram bot."""
    # Validate config
    config.validate()

    # Initialize database
    init_db()

    # Build application
    app = Application.builder().token(config.telegram_bot_token).build()

    # Create shared aggregator
    aggregator = FlightAggregator()

    # Inject aggregator into search handler
    search.set_aggregator(aggregator)

    # Register all handlers
    start.register(app)
    trips.register(app)
    search.register(app)
    settings.register(app)

    # Schedule price checks
    async def price_check_job() -> None:
        """Wrapper invoked by APScheduler."""
        await run_price_check(app.bot, aggregator)

    # Post-init hook: start scheduler after bot is ready
    async def post_init(application: Application) -> None:
        start_scheduler(price_check_job)
        logger.info("🦅 FareHawk is online!")

    async def post_shutdown(application: Application) -> None:
        stop_scheduler()
        await aggregator.close()
        logger.info("🦅 FareHawk shut down gracefully")

    app.post_init = post_init
    app.post_shutdown = post_shutdown

    # Run polling (blocks until stopped)
    logger.info("Starting FareHawk bot…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
