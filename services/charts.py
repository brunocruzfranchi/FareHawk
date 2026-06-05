"""Price history chart generation using matplotlib."""

import io
import logging
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from sqlalchemy.orm import Session
from core.models import PriceSnapshot

logger = logging.getLogger(__name__)


def generate_price_chart(
    session: Session,
    trip_id: int,
    currency: str = "USD",
    *,
    budget: float | None = None,
    days: int | None = None,
    title: str = "Price History",
) -> io.BytesIO | None:
    """Generate a PNG price-history chart for a trip.

    Returns a BytesIO buffer with the PNG data, or None if insufficient data.
    """
    query = (
        session.query(PriceSnapshot)
        .filter(PriceSnapshot.trip_id == trip_id)
        .order_by(PriceSnapshot.timestamp.asc())
    )

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(PriceSnapshot.timestamp >= cutoff)

    snapshots = query.all()

    if len(snapshots) < 2:
        return None  # Need at least 2 points for a chart

    timestamps = [s.timestamp for s in snapshots]
    prices = [s.price for s in snapshots]

    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor="#0F172A")
    ax.set_facecolor("#111827")

    line_color = "#38BDF8"
    fill_color = "#0EA5E9"
    text_color = "#E5E7EB"
    muted_color = "#94A3B8"
    grid_color = "#334155"
    low_color = "#22C55E"
    high_color = "#F97316"
    latest_color = "#FACC15"
    budget_color = "#A78BFA"

    ax.plot(
        timestamps,
        prices,
        marker="o",
        linewidth=2.5,
        color=line_color,
        markersize=5,
        markerfacecolor="#E0F2FE",
        markeredgecolor=line_color,
    )
    ax.fill_between(timestamps, prices, alpha=0.18, color=fill_color)

    min_price = min(prices)
    max_price = max(prices)
    latest_price = prices[-1]
    min_idx = prices.index(min_price)
    max_idx = prices.index(max_price)
    latest_idx = len(prices) - 1

    ax.scatter(timestamps[min_idx], min_price, color=low_color, s=55, zorder=4)
    ax.scatter(timestamps[max_idx], max_price, color=high_color, s=45, zorder=4)
    ax.scatter(timestamps[latest_idx], latest_price, color=latest_color, s=65, zorder=5)

    def annotate(label: str, idx: int, price: float, color: str, offset: tuple[int, int]) -> None:
        ax.annotate(
            label,
            xy=(timestamps[idx], price),
            xytext=offset,
            textcoords="offset points",
            fontsize=9,
            color=color,
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=color, linewidth=1.2),
            bbox=dict(boxstyle="round,pad=0.25", fc="#0F172A", ec=color, alpha=0.85),
        )

    annotate(f"Low: {min_price:,.0f}", min_idx, min_price, low_color, (12, -26))
    if max_idx != min_idx:
        annotate(f"High: {max_price:,.0f}", max_idx, max_price, high_color, (12, 18))
    annotate(f"Latest: {latest_price:,.0f}", latest_idx, latest_price, latest_color, (12, 8))

    if budget is not None:
        ax.axhline(budget, color=budget_color, linestyle="--", linewidth=1.5, alpha=0.9)
        ax.text(
            timestamps[0],
            budget,
            f" Budget {budget:,.0f}",
            color=budget_color,
            fontsize=9,
            fontweight="bold",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.2", fc="#0F172A", ec=budget_color, alpha=0.8),
        )

    ax.set_title(title, fontsize=15, fontweight="bold", color=text_color, pad=14)
    ax.set_ylabel(f"Price ({currency})", fontsize=11, color=muted_color)
    ax.set_xlabel("Date", fontsize=11, color=muted_color)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=6))
    fig.autofmt_xdate()

    ax.grid(True, alpha=0.45, color=grid_color, linestyle="--", linewidth=0.8)
    ax.tick_params(axis="both", colors=muted_color)
    for spine in ax.spines.values():
        spine.set_color(grid_color)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf
