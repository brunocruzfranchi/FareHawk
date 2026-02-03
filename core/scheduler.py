"""APScheduler setup for periodic price checks."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.config import config

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(price_check_callback) -> None:
    """Start the scheduler with the price-check job."""
    scheduler.add_job(
        price_check_callback,
        trigger=IntervalTrigger(hours=config.default_check_interval_hours),
        id="price_checker",
        name="Periodic flight price checker",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(
        "Scheduler started — price checks every %d hours",
        config.default_check_interval_hours,
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
