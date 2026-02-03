"""SQLAlchemy ORM models for FareHawk."""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Boolean, Date,
    DateTime, Text, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    language = Column(String(5), nullable=False, default="en")
    currency = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    origin = Column(String(10), nullable=False)          # IATA code or city
    destination = Column(String(10), nullable=False)      # IATA code or city
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    flex_days = Column(Integer, nullable=False, default=3)
    max_price = Column(Float, nullable=True)
    flight_type = Column(String(10), nullable=False, default="round")  # "round" or "oneway"
    return_date_from = Column(Date, nullable=True)
    return_date_to = Column(Date, nullable=True)
    direct_only = Column(Boolean, nullable=False, default=False)
    max_stopovers = Column(Integer, nullable=True)
    check_interval_hours = Column(Integer, nullable=False, default=3)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="trips")
    snapshots = relationship("PriceSnapshot", back_populates="trip", cascade="all, delete-orphan",
                             order_by="PriceSnapshot.timestamp.desc()")
    alerts = relationship("Alert", back_populates="trip", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Trip(id={self.id}, name='{self.name}', {self.origin}→{self.destination})>"


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    airline = Column(String(100), nullable=True)
    stopovers = Column(Integer, nullable=False, default=0)
    duration_minutes = Column(Integer, nullable=True)
    source = Column(String(50), nullable=False, default="kiwi")
    flight_details = Column(Text, nullable=True)  # JSON blob
    outbound_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)

    trip = relationship("Trip", back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<PriceSnapshot(trip_id={self.trip_id}, price={self.price} {self.currency})>"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price_drop / new_low / threshold
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    previous_price = Column(Float, nullable=True)
    details = Column(Text, nullable=True)  # JSON blob
    sent = Column(Boolean, nullable=False, default=False)

    trip = relationship("Trip", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(trip_id={self.trip_id}, type='{self.alert_type}', price={self.price})>"
