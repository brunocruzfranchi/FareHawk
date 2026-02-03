"""Weekly digest — generates a summary for each user with active trips."""

import logging
from datetime import datetime, timedelta

from telegram import Bot

from core.database import get_session
from core.models import User, Trip, PriceSnapshot
from bot.i18n import t

logger = logging.getLogger(__name__)


async def send_weekly_digest(bot: Bot) -> None:
    """Generate and send a weekly digest to each user with active trips."""
    logger.info("Starting weekly digest")

    with get_session() as session:
        users = session.query(User).all()

        for user in users:
            try:
                trips = (
                    session.query(Trip)
                    .filter(Trip.user_id == user.id, Trip.active.is_(True))
                    .all()
                )

                if not trips:
                    continue

                lang = user.language or "en"
                currency = user.currency or "USD"
                one_week_ago = datetime.utcnow() - timedelta(days=7)

                msg = t("digest_header", lang)

                for trip in trips:
                    # Get latest snapshot
                    latest = (
                        session.query(PriceSnapshot)
                        .filter(PriceSnapshot.trip_id == trip.id)
                        .order_by(PriceSnapshot.timestamp.desc())
                        .first()
                    )

                    if not latest:
                        msg += t("digest_no_data", lang,
                                 name=trip.name,
                                 origin=trip.origin,
                                 destination=trip.destination)
                        continue

                    # Get price from a week ago (closest snapshot)
                    week_ago_snapshot = (
                        session.query(PriceSnapshot)
                        .filter(
                            PriceSnapshot.trip_id == trip.id,
                            PriceSnapshot.timestamp <= one_week_ago,
                        )
                        .order_by(PriceSnapshot.timestamp.desc())
                        .first()
                    )

                    # Determine trend
                    if week_ago_snapshot:
                        diff = latest.price - week_ago_snapshot.price
                        if diff < -1:
                            trend = t("trend_down", lang)
                            change = f"-{abs(diff):.2f} {currency}"
                        elif diff > 1:
                            trend = t("trend_up", lang)
                            change = f"+{diff:.2f} {currency}"
                        else:
                            trend = t("trend_stable", lang)
                            change = f"~0 {currency}"
                    else:
                        trend = t("trend_stable", lang)
                        change = "N/A (no previous data)"

                    msg += t("digest_trip", lang,
                             name=trip.name,
                             origin=trip.origin,
                             destination=trip.destination,
                             price=f"{latest.price:.2f}",
                             currency=currency,
                             trend=trend,
                             change=change)

                msg += t("digest_footer", lang)

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=msg,
                    parse_mode="Markdown",
                )
                logger.info("Sent weekly digest to user %d", user.telegram_id)

            except Exception:
                logger.exception("Failed to send digest to user %d", user.telegram_id)

    logger.info("Weekly digest complete")
