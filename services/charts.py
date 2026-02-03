"""Price history chart generation using matplotlib."""

import io
import logging
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from sqlalchemy.orm import Session
from core.models import PriceSnapshot

logger = logging.getLogger(__name__)


def generate_price_chart(session: Session, trip_id: int, currency: str = "USD") -> io.BytesIO | None:
    """Generate a PNG price-history chart for a trip.

    Returns a BytesIO buffer with the PNG data, or None if insufficient data.
    """
    snapshots = (
        session.query(PriceSnapshot)
        .filter(PriceSnapshot.trip_id == trip_id)
        .order_by(PriceSnapshot.timestamp.asc())
        .all()
    )

    if len(snapshots) < 2:
        return None  # Need at least 2 points for a chart

    timestamps = [s.timestamp for s in snapshots]
    prices = [s.price for s in snapshots]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(timestamps, prices, marker="o", linewidth=2, color="#2196F3", markersize=4)
    ax.fill_between(timestamps, prices, alpha=0.1, color="#2196F3")

    ax.set_title("Price History", fontsize=14, fontweight="bold")
    ax.set_ylabel(f"Price ({currency})", fontsize=11)
    ax.set_xlabel("Date", fontsize=11)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    fig.autofmt_xdate()

    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Highlight min price
    min_price = min(prices)
    min_idx = prices.index(min_price)
    ax.annotate(
        f"Low: {min_price:.0f}",
        xy=(timestamps[min_idx], min_price),
        xytext=(10, -20),
        textcoords="offset points",
        fontsize=9,
        color="green",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="green"),
    )

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf
