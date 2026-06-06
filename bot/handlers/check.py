"""Handler for /check — force immediate price check."""

import json
import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.i18n import t
from core.database import get_or_create_user, get_session
from core.models import User, Trip, PriceSnapshot
from providers.aggregator import FlightAggregator
from providers.base import FlightResult
from core.time import utc_now

logger = logging.getLogger(__name__)

# Shared aggregator — set from main.py
_aggregator: FlightAggregator | None = None


def set_aggregator(agg: FlightAggregator) -> None:
    global _aggregator
    _aggregator = agg


def _generate_booking_link_fallback(origin: str, dest: str, outbound_date=None) -> str:
    """Generate a Google Flights fallback link."""
    from urllib.parse import quote
    date_str = outbound_date.isoformat() if outbound_date else ""
    q = f"Flights from {origin} to {dest}"
    if date_str:
        q += f" on {date_str}"
    return f"https://www.google.com/travel/flights?q={quote(q)}"


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /check [trip_id] — force price check."""
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    lang = user.language
    currency = user.currency

    if _aggregator is None:
        await update.message.reply_text(t("error", lang), parse_mode="Markdown")
        return

    args = context.args or []

    with get_session() as session:
        if args:
            # Check specific trip
            try:
                trip_id = int(args[0])
            except ValueError:
                await update.message.reply_text(
                    t("check_trip_not_found", lang, trip_id=args[0]),
                    parse_mode="Markdown",
                )
                return

            trip = (
                session.query(Trip)
                .join(User)
                .filter(Trip.id == trip_id, User.telegram_id == user.telegram_id)
                .first()
            )
            if not trip:
                await update.message.reply_text(
                    t("check_trip_not_found", lang, trip_id=trip_id),
                    parse_mode="Markdown",
                )
                return
            trips_to_check = [trip]
        else:
            # Check all active trips
            trips_to_check = (
                session.query(Trip)
                .join(User)
                .filter(User.telegram_id == user.telegram_id, Trip.active.is_(True))
                .all()
            )

        if not trips_to_check:
            await update.message.reply_text(t("check_no_trips", lang), parse_mode="Markdown")
            return

        await update.message.reply_text(t("check_header", lang), parse_mode="Markdown")

        for trip in trips_to_check:
            await update.message.reply_text(
                t("check_searching", lang, name=trip.name, origin=trip.origin, destination=trip.destination),
                parse_mode="Markdown",
            )

            try:
                results = await _aggregator.search(
                    origin=trip.origin,
                    destination=trip.destination,
                    date_from=trip.date_from,
                    date_to=trip.date_to,
                    currency=currency,
                    direct_only=trip.direct_only,
                    max_stopovers=trip.max_stopovers,
                    limit=3,
                    flight_type=getattr(trip, 'flight_type', 'round') or 'round',
                    return_date_from=getattr(trip, 'return_date_from', None),
                    return_date_to=getattr(trip, 'return_date_to', None),
                )

                if not results:
                    await update.message.reply_text(
                        t("check_no_results", lang, name=trip.name),
                        parse_mode="Markdown",
                    )
                    continue

                # Save best result as snapshot
                best = results[0]
                snapshot = PriceSnapshot(
                    trip_id=trip.id,
                    timestamp=utc_now(),
                    price=best.price,
                    currency=currency,
                    airline=best.airline,
                    stopovers=best.stopovers,
                    duration_minutes=best.duration_minutes,
                    source=best.source,
                    flight_details=json.dumps(best.flight_details),
                    outbound_date=best.outbound_date,
                    return_date=best.return_date,
                )
                session.add(snapshot)
                session.flush()

                # Show results
                flight_type = getattr(trip, 'flight_type', 'round') or 'round'
                for r in results[:3]:
                    link = r.booking_link or _generate_booking_link_fallback(
                        r.origin, r.destination, r.outbound_date,
                    )
                    return_str = r.return_date.strftime("%d/%m/%Y") if r.return_date else "—"
                    outbound_str = r.outbound_date.strftime("%d/%m/%Y") if r.outbound_date else "—"
                    type_label = "🔄 Round trip" if flight_type == "round" else "➡️ One-way"
                    dates_display = f"{outbound_str} → {return_str}" if flight_type == "round" else outbound_str

                    text = t("check_result", lang,
                             name=trip.name,
                             airline=r.airline,
                             price=f"{r.price:.2f}",
                             currency=r.currency,
                             dates=dates_display,
                             flight_type=type_label,
                             duration=r.duration_display,
                             stopovers=r.stopovers,
                             link=link)
                    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)

            except Exception:
                logger.exception("Check failed for trip %d", trip.id)
                await update.message.reply_text(t("error", lang), parse_mode="Markdown")

        await update.message.reply_text(t("check_complete", lang), parse_mode="Markdown")


def register(app) -> None:
    """Register check handlers."""
    app.add_handler(CommandHandler("check", check_command))
