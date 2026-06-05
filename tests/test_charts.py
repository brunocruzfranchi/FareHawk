from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base, PriceSnapshot, Trip, User
from services.charts import generate_price_chart


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _trip(session, *, max_price=None) -> Trip:
    user = User(telegram_id=12345, username="alice")
    trip = Trip(
        user=user,
        name="Barcelona",
        origin="JFK",
        destination="BCN",
        date_from=datetime(2026, 10, 17).date(),
        date_to=datetime(2026, 10, 17).date(),
        max_price=max_price,
    )
    session.add_all([user, trip])
    session.flush()
    return trip


def test_generate_price_chart_requires_two_snapshots():
    with _session() as session:
        trip = _trip(session)
        session.add(
            PriceSnapshot(
                trip_id=trip.id,
                timestamp=datetime(2026, 6, 1, 12, 0, 0),
                price=500,
                currency="USD",
            )
        )
        session.flush()

        assert generate_price_chart(session, trip.id, "USD") is None


def test_generate_price_chart_returns_png_with_budget_line_and_recent_window():
    with _session() as session:
        trip = _trip(session, max_price=450)
        base = datetime(2026, 6, 1, 12, 0, 0)
        prices = [510, 480, 430, 460]
        for index, price in enumerate(prices):
            session.add(
                PriceSnapshot(
                    trip_id=trip.id,
                    timestamp=base + timedelta(days=index),
                    price=price,
                    currency="USD",
                )
            )
        session.flush()

        chart = generate_price_chart(
            session,
            trip.id,
            "USD",
            budget=trip.max_price,
            days=30,
            title="JFK → BCN Price History",
        )

        assert chart is not None
        data = chart.getvalue()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        assert len(data) > 10_000
