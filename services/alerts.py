"""Alert evaluation logic — determines when to notify users."""

import json
import logging
from datetime import datetime
from urllib.parse import quote

from sqlalchemy.orm import Session

from core.models import Trip, PriceSnapshot, Alert
from providers.base import FlightResult
from core.config import config

logger = logging.getLogger(__name__)


def evaluate_alerts(
    session: Session,
    trip: Trip,
    best: FlightResult,
    currency: str,
) -> list[Alert]:
    """Evaluate alert conditions for a trip given the latest best result.

    Returns a list of Alert objects (already added to session) that should be sent.
    """
    alerts: list[Alert] = []

    latest_snapshot_id_row = (
        session.query(PriceSnapshot.id)
        .filter(PriceSnapshot.trip_id == trip.id)
        .order_by(PriceSnapshot.timestamp.desc(), PriceSnapshot.id.desc())
        .first()
    )
    latest_snapshot_id = latest_snapshot_id_row[0] if latest_snapshot_id_row else None

    previous_snapshots = session.query(PriceSnapshot).filter(PriceSnapshot.trip_id == trip.id)
    if latest_snapshot_id is not None:
        previous_snapshots = previous_snapshots.filter(PriceSnapshot.id != latest_snapshot_id)

    # Fetch previous snapshots for comparison. The caller inserts the current
    # snapshot before evaluating alerts, so comparisons must exclude it.
    prev_snapshot = (
        previous_snapshots
        .order_by(PriceSnapshot.timestamp.desc(), PriceSnapshot.id.desc())
        .first()
    )

    # Historical minimum before the current result.
    min_price_row = (
        previous_snapshots
        .with_entities(PriceSnapshot.price)
        .order_by(PriceSnapshot.price.asc())
        .first()
    )
    historical_min = min_price_row[0] if min_price_row else None

    # Build fallback booking link if none provided
    booking_link = best.booking_link
    if not booking_link:
        q = f"Flights from {best.origin} to {best.destination}"
        if best.outbound_date:
            q += f" on {best.outbound_date.isoformat()}"
        booking_link = f"https://www.google.com/travel/flights?q={quote(q)}"

    details = json.dumps({
        "airline": best.airline,
        "stopovers": best.stopovers,
        "duration": best.duration_display,
        "outbound": str(best.outbound_date),
        "return_date": str(best.return_date) if best.return_date else None,
        "link": booking_link,
    })

    # 1) Price drop > threshold %
    if prev_snapshot and prev_snapshot.price > 0:
        drop_pct = ((prev_snapshot.price - best.price) / prev_snapshot.price) * 100
        if drop_pct >= config.price_drop_threshold_pct:
            alert = Alert(
                trip_id=trip.id,
                alert_type="price_drop",
                triggered_at=datetime.utcnow(),
                price=best.price,
                previous_price=prev_snapshot.price,
                details=details,
                sent=False,
            )
            session.add(alert)
            alerts.append(alert)
            logger.info("Alert: price_drop %.1f%% for trip %d", drop_pct, trip.id)

    # 2) New all-time low
    if historical_min is not None and best.price < historical_min:
        alert = Alert(
            trip_id=trip.id,
            alert_type="new_low",
            triggered_at=datetime.utcnow(),
            price=best.price,
            previous_price=historical_min,
            details=details,
            sent=False,
        )
        session.add(alert)
        alerts.append(alert)
        logger.info("Alert: new_low for trip %d (%.2f < %.2f)", trip.id, best.price, historical_min)

    # 3) Under budget threshold
    if trip.max_price and best.price <= trip.max_price:
        # Only alert once per exact observed price.
        recent_threshold = (
            session.query(Alert)
            .filter(
                Alert.trip_id == trip.id,
                Alert.alert_type == "threshold",
                Alert.price == best.price,
            )
            .first()
        )
        if not recent_threshold:
            alert = Alert(
                trip_id=trip.id,
                alert_type="threshold",
                triggered_at=datetime.utcnow(),
                price=best.price,
                previous_price=None,
                details=details,
                sent=False,
            )
            session.add(alert)
            alerts.append(alert)
            logger.info("Alert: threshold for trip %d (%.2f <= %.2f)", trip.id, best.price, trip.max_price)

    return alerts
