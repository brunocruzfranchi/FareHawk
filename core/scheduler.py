"""APScheduler setup for periodic price checks and weekly digest."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from core.config import config

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(price_check_callback, digest_callback=None) -> None:
    """Start the scheduler with the price-check job and optional digest."""
    scheduler.add_job(
        price_check_callback,
        trigger=IntervalTrigger(hours=config.default_check_interval_hours),
        id="price_checker",
        name="Periodic flight price checker",
        replace_existing=True,
        max_instances=1,
    )

    if digest_callback:
        scheduler.add_job(
            digest_callback,
            trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_digest",
            name="Weekly flight digest",
            replace_existing=True,
            max_instances=1,
        )
        logger.info("Weekly digest scheduled for Mondays at 09:00 UTC")

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
