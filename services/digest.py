"""Weekly digest — generates a summary for each user with active trips."""

import logging
from datetime import datetime, timedelta

from core.time import utc_now

from telegram import Bot

from core.database import get_session
from core.models import User, Trip, PriceSnapshot
from bot.i18n import t

logger = logging.getLogger(__name__)


def _format_budget_status(trip: Trip, latest: PriceSnapshot, currency: str) -> str:
    """Return a short budget status line for digest output."""
    if trip.max_price is None:
        return ""

    diff = trip.max_price - latest.price
    if diff >= 0:
        return f"   🎯 Under budget by {diff:.2f} {currency}\n"
    return f"   ⚠️ Over budget by {abs(diff):.2f} {currency}\n"


def build_weekly_digest_message(session, user: User, *, now: datetime | None = None) -> str:
    """Build the weekly digest message for a single user.

    Returns an empty string when the user has no active trips.
    """
    trips = (
        session.query(Trip)
        .filter(Trip.user_id == user.id, Trip.active.is_(True))
        .all()
    )
    if not trips:
        return ""

    lang = user.language or "en"
    currency = user.currency or "USD"
    now = now or utc_now()
    one_week_ago = now - timedelta(days=7)

    msg = t("digest_header", lang)
    biggest_drop: tuple[float, str] | None = None

    for trip in trips:
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

        week_ago_snapshot = (
            session.query(PriceSnapshot)
            .filter(
                PriceSnapshot.trip_id == trip.id,
                PriceSnapshot.timestamp <= one_week_ago,
            )
            .order_by(PriceSnapshot.timestamp.desc())
            .first()
        )

        if week_ago_snapshot:
            diff = latest.price - week_ago_snapshot.price
            if diff < -1:
                trend = t("trend_down", lang)
                change = f"-{abs(diff):.2f} {currency}"
                drop = abs(diff)
                if biggest_drop is None or drop > biggest_drop[0]:
                    biggest_drop = (drop, trip.name)
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
        msg += _format_budget_status(trip, latest, currency)
        msg += "\n"

    if biggest_drop:
        amount, trip_name = biggest_drop
        msg += f"🏆 Biggest drop: *{amount:.2f} {currency}* — {trip_name}\n\n"

    msg += t("digest_footer", lang)
    return msg


async def send_weekly_digest(bot: Bot) -> None:
    """Generate and send a weekly digest to each user with active trips."""
    logger.info("Starting weekly digest")

    with get_session() as session:
        users = session.query(User).all()

        for user in users:
            try:
                msg = build_weekly_digest_message(session, user)
                if not msg:
                    continue

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=msg,
                    parse_mode="Markdown",
                )
                logger.info("Sent weekly digest to user %d", user.telegram_id)

            except Exception:
                logger.exception("Failed to send digest to user %d", user.telegram_id)

    logger.info("Weekly digest complete")
