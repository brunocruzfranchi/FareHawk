from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base, PriceSnapshot, Trip, User
from providers.base import FlightResult
from services.alerts import evaluate_alerts


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        yield db


def _trip(session, *, max_price=None) -> Trip:
    user = User(telegram_id=12345, username="alice")
    trip = Trip(
        user=user,
        name="Barcelona",
        origin="JFK",
        destination="BCN",
        date_from=date(2026, 10, 17),
        date_to=date(2026, 10, 17),
        max_price=max_price,
    )
    session.add_all([user, trip])
    session.flush()
    return trip


def _result(price: float) -> FlightResult:
    return FlightResult(
        price=price,
        currency="USD",
        airline="Test Air",
        origin="JFK",
        destination="BCN",
        outbound_date=date(2026, 10, 17),
        return_date=None,
        stopovers=0,
        duration_minutes=480,
        source="test",
    )


def test_new_low_alert_compares_against_prior_snapshots(session):
    trip = _trip(session)
    now = datetime(2026, 6, 1, 12, 0, 0)
    session.add(
        PriceSnapshot(
            trip_id=trip.id,
            timestamp=now - timedelta(hours=3),
            price=500,
            currency="USD",
        )
    )
    session.add(
        PriceSnapshot(
            trip_id=trip.id,
            timestamp=now,
            price=400,
            currency="USD",
        )
    )
    session.flush()

    alerts = evaluate_alerts(session, trip, _result(400), "USD")

    assert {alert.alert_type for alert in alerts} == {"price_drop", "new_low"}


def test_first_snapshot_does_not_trigger_history_alerts(session):
    trip = _trip(session)
    session.add(
        PriceSnapshot(
            trip_id=trip.id,
            timestamp=datetime(2026, 6, 1, 12, 0, 0),
            price=400,
            currency="USD",
        )
    )
    session.flush()

    alerts = evaluate_alerts(session, trip, _result(400), "USD")

    assert [alert.alert_type for alert in alerts] == []
