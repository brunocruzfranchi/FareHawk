from datetime import datetime, timedelta, date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base, PriceSnapshot, Trip, User
from services.digest import build_weekly_digest_message


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_build_weekly_digest_message_includes_best_weekly_drop_and_budget_status():
    with _session() as session:
        user = User(telegram_id=123, username="alice", language="en", currency="USD")
        trip = Trip(
            user=user,
            name="Barcelona",
            origin="JFK",
            destination="BCN",
            date_from=date(2026, 10, 17),
            date_to=date(2026, 10, 17),
            max_price=450,
        )
        session.add_all([user, trip])
        session.flush()

        now = datetime(2026, 6, 8, 12, 0, 0)
        session.add(
            PriceSnapshot(
                trip_id=trip.id,
                timestamp=now - timedelta(days=8),
                price=520,
                currency="USD",
            )
        )
        session.add(
            PriceSnapshot(
                trip_id=trip.id,
                timestamp=now,
                price=430,
                currency="USD",
            )
        )
        session.flush()

        message = build_weekly_digest_message(session, user, now=now)

        assert "Biggest drop: *90.00 USD*" in message
        assert "🎯 Under budget by 20.00 USD" in message
        assert "📉 Change: -90.00 USD" in message


def test_build_weekly_digest_message_reports_no_active_trips():
    with _session() as session:
        user = User(telegram_id=123, username="alice", language="en", currency="USD")
        session.add(user)
        session.flush()

        message = build_weekly_digest_message(session, user)

        assert message == ""
