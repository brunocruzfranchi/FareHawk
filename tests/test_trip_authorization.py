from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.handlers.trips import _get_user_trip
from core.models import Base, Trip, User


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        yield db


def test_get_user_trip_enforces_telegram_owner(session):
    owner = User(telegram_id=111, username="owner")
    other = User(telegram_id=222, username="other")
    trip = Trip(
        user=owner,
        name="Lisbon",
        origin="JFK",
        destination="LIS",
        date_from=date(2026, 10, 17),
        date_to=date(2026, 10, 20),
    )
    session.add_all([owner, other, trip])
    session.flush()

    assert _get_user_trip(session, trip.id, owner.telegram_id) == trip
    assert _get_user_trip(session, trip.id, other.telegram_id) is None
