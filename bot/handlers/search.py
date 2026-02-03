"""Handler for /search — quick one-off flight search."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.i18n import t
from core.database import get_or_create_user
from providers.aggregator import FlightAggregator

logger = logging.getLogger(__name__)

# Shared aggregator instance — will be set from main.py
_aggregator: FlightAggregator | None = None


def set_aggregator(agg: FlightAggregator) -> None:
    global _aggregator
    _aggregator = agg


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search <origin> <dest> <DD/MM/YYYY>."""
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    lang = user.language
    currency = user.currency

    args = context.args or []
    if len(args) < 3:
        await update.message.reply_text(t("search_usage", lang), parse_mode="Markdown")
        return

    origin = args[0].upper()
    dest = args[1].upper()
    date_str = args[2]

    try:
        search_date = datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text(t("search_usage", lang), parse_mode="Markdown")
        return

    await update.message.reply_text(
        t("search_searching", lang, origin=origin, destination=dest, date=date_str),
        parse_mode="Markdown",
    )

    if _aggregator is None:
        await update.message.reply_text(t("error", lang), parse_mode="Markdown")
        return

    try:
        results = await _aggregator.search(
            origin=origin,
            destination=dest,
            date_from=search_date,
            date_to=search_date,
            currency=currency,
            limit=5,
        )
    except Exception:
        logger.exception("Search failed for %s→%s", origin, dest)
        await update.message.reply_text(t("error", lang), parse_mode="Markdown")
        return

    if not results:
        await update.message.reply_text(t("search_no_results", lang), parse_mode="Markdown")
        return

    for r in results[:5]:
        text = t("search_result", lang,
                 airline=r.airline,
                 price=f"{r.price:.2f}",
                 currency=r.currency,
                 outbound_date=r.outbound_date.strftime("%d/%m/%Y") if r.outbound_date else "—",
                 duration=r.duration_display,
                 stopovers=r.stopovers,
                 link=r.booking_link or "#")
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)


def register(app) -> None:
    """Register search handlers."""
    app.add_handler(CommandHandler("search", search_command))
