"""Periodic price-check service — queries providers for every active trip."""

import json
import logging
from datetime import datetime
from urllib.parse import quote

from telegram import Bot

from core.database import get_session
from core.models import Trip, PriceSnapshot, User
from providers.aggregator import FlightAggregator
from services.alerts import evaluate_alerts
from bot.i18n import t

logger = logging.getLogger(__name__)


async def run_price_check(bot: Bot, aggregator: FlightAggregator) -> None:
    """Check prices for all active trips, save snapshots, evaluate & send alerts."""
    logger.info("Starting periodic price check")

    with get_session() as session:
        trips = session.query(Trip).filter(Trip.active.is_(True)).all()
        logger.info("Found %d active trips to check", len(trips))

        for trip in trips:
            try:
                user = session.query(User).filter(User.id == trip.user_id).first()
                if not user:
                    continue

                currency = user.currency or "USD"
                lang = user.language or "en"

                results = await aggregator.search(
                    origin=trip.origin,
                    destination=trip.destination,
                    date_from=trip.date_from,
                    date_to=trip.date_to,
                    currency=currency,
                    direct_only=trip.direct_only,
                    max_stopovers=trip.max_stopovers,
                    limit=5,
                    flight_type=getattr(trip, 'flight_type', 'round') or 'round',
                    return_date_from=getattr(trip, 'return_date_from', None),
                    return_date_to=getattr(trip, 'return_date_to', None),
                )

                if not results:
                    logger.info("No results for trip %d (%s→%s)", trip.id, trip.origin, trip.destination)
                    continue

                best = results[0]

                # Save snapshot
                snapshot = PriceSnapshot(
                    trip_id=trip.id,
                    timestamp=datetime.utcnow(),
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

                # Evaluate alerts
                alerts = evaluate_alerts(session, trip, best, currency)

                # Send alert messages
                for alert in alerts:
                    try:
                        details = json.loads(alert.details) if alert.details else {}
                        msg = _format_alert_message(alert, trip, currency, lang, details)
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=msg,
                            parse_mode="Markdown",
                            disable_web_page_preview=True,
                        )
                        alert.sent = True
                        logger.info("Sent %s alert to user %d for trip %d",
                                    alert.alert_type, user.telegram_id, trip.id)
                    except Exception:
                        logger.exception("Failed to send alert to user %d", user.telegram_id)

            except Exception:
                logger.exception("Error checking trip %d", trip.id)

    logger.info("Price check complete")


def _format_alert_message(alert, trip, currency: str, lang: str, details: dict) -> str:
    """Format an alert into a Telegram message string."""
    common = {
        "name": trip.name,
        "price": f"{alert.price:.2f}",
        "currency": currency,
        "airline": details.get("airline", "—"),
        "stopovers": details.get("stopovers", 0),
        "duration": details.get("duration", "—"),
        "outbound": details.get("outbound", "—"),
        "return_date": details.get("return_date", "—"),
        "link": details.get("link", "#"),
    }

    if alert.alert_type == "price_drop":
        pct = 0.0
        if alert.previous_price and alert.previous_price > 0:
            pct = ((alert.previous_price - alert.price) / alert.previous_price) * 100
        return t("alert_price_drop", lang,
                 prev_price=f"{alert.previous_price:.2f}" if alert.previous_price else "—",
                 pct=f"{pct:.1f}", **common)

    elif alert.alert_type == "new_low":
        return t("alert_new_low", lang, **common)

    elif alert.alert_type == "threshold":
        return t("alert_threshold", lang,
                 budget=f"{trip.max_price:.2f}" if trip.max_price else "—",
                 **common)

    return f"📢 Alert for {trip.name}: {alert.price} {currency}"
