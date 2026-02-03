"""Handlers for trip CRUD: /newtrip wizard, /trips, /trip, pause, resume, delete."""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from bot.i18n import t
from bot.keyboards.inline import (
    yes_no_keyboard,
    confirm_cancel_keyboard,
    trip_list_keyboard,
    trip_actions_keyboard,
    confirm_delete_keyboard,
)
from core.database import get_or_create_user, get_session
from core.models import User, Trip, PriceSnapshot
from services.charts import generate_price_chart

logger = logging.getLogger(__name__)

# Conversation states
NAME, ORIGIN, DEST, DATES, FLEX, PRICE, DIRECT, CONFIRM = range(8)


def _get_lang(user_id: int) -> str:
    user = get_or_create_user(user_id)
    return user.language


def _get_currency(user_id: int) -> str:
    user = get_or_create_user(user_id)
    return user.currency


# ── /newtrip Wizard ──────────────────────────────────────────────────

async def newtrip_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data["trip"] = {}
    await update.message.reply_text(t("trip_name_ask", lang), parse_mode="Markdown")
    return NAME


async def trip_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data["trip"]["name"] = update.message.text.strip()
    await update.message.reply_text(t("trip_origin_ask", lang), parse_mode="Markdown")
    return ORIGIN


async def trip_origin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data["trip"]["origin"] = update.message.text.strip().upper()
    await update.message.reply_text(t("trip_dest_ask", lang), parse_mode="Markdown")
    return DEST


async def trip_dest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data["trip"]["destination"] = update.message.text.strip().upper()
    await update.message.reply_text(t("trip_dates_ask", lang), parse_mode="Markdown")
    return DATES


async def trip_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        await update.message.reply_text(t("trip_dates_invalid", lang), parse_mode="Markdown")
        return DATES

    try:
        date_from = datetime.strptime(parts[0], "%d/%m/%Y").date()
        date_to = datetime.strptime(parts[1], "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text(t("trip_dates_invalid", lang), parse_mode="Markdown")
        return DATES

    context.user_data["trip"]["date_from"] = date_from
    context.user_data["trip"]["date_to"] = date_to
    await update.message.reply_text(t("trip_flex_ask", lang), parse_mode="Markdown")
    return FLEX


async def trip_flex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    currency = _get_currency(update.effective_user.id)
    text = update.message.text.strip()

    if text == "/skip":
        context.user_data["trip"]["flex_days"] = 3
    else:
        try:
            context.user_data["trip"]["flex_days"] = int(text)
        except ValueError:
            context.user_data["trip"]["flex_days"] = 3

    await update.message.reply_text(
        t("trip_price_ask", lang, currency=currency), parse_mode="Markdown"
    )
    return PRICE


async def trip_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    text = update.message.text.strip()

    if text == "/skip":
        context.user_data["trip"]["max_price"] = None
    else:
        try:
            context.user_data["trip"]["max_price"] = float(text)
        except ValueError:
            context.user_data["trip"]["max_price"] = None

    await update.message.reply_text(
        t("trip_direct_ask", lang),
        parse_mode="Markdown",
        reply_markup=yes_no_keyboard(lang),
    )
    return DIRECT


async def trip_direct_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)
    currency = _get_currency(query.from_user.id)

    context.user_data["trip"]["direct_only"] = query.data == "yn:yes"

    td = context.user_data["trip"]
    max_price_str = f"{td['max_price']:.2f} {currency}" if td["max_price"] else "—"
    direct_str = t("yes", lang) if td["direct_only"] else t("no", lang)

    await query.edit_message_text(
        t("trip_confirm", lang,
          name=td["name"],
          origin=td["origin"],
          destination=td["destination"],
          date_from=td["date_from"].strftime("%d/%m/%Y"),
          date_to=td["date_to"].strftime("%d/%m/%Y"),
          flex_days=td["flex_days"],
          max_price=max_price_str,
          direct_only=direct_str),
        parse_mode="Markdown",
        reply_markup=confirm_cancel_keyboard(lang),
    )
    return CONFIRM


async def trip_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)

    if query.data == "confirm:cancel":
        await query.edit_message_text(t("trip_cancelled", lang), parse_mode="Markdown")
        context.user_data.pop("trip", None)
        return ConversationHandler.END

    td = context.user_data.pop("trip", {})
    user = get_or_create_user(query.from_user.id, query.from_user.username)

    with get_session() as session:
        trip = Trip(
            user_id=user.id,
            name=td["name"],
            origin=td["origin"],
            destination=td["destination"],
            date_from=td["date_from"],
            date_to=td["date_to"],
            flex_days=td.get("flex_days", 3),
            max_price=td.get("max_price"),
            direct_only=td.get("direct_only", False),
        )
        session.add(trip)

    await query.edit_message_text(
        t("trip_saved", lang, name=td["name"]),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data.pop("trip", None)
    await update.message.reply_text(t("trip_cancelled", lang), parse_mode="Markdown")
    return ConversationHandler.END


# ── /trips ────────────────────────────────────────────────────────────

async def trips_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    lang = user.language

    with get_session() as session:
        trips = session.query(Trip).filter(Trip.user_id == user.id).all()
        if not trips:
            await update.message.reply_text(t("no_trips", lang), parse_mode="Markdown")
            return

        # Detach for keyboard
        session.expunge_all()

    await update.message.reply_text(
        t("trips_header", lang),
        parse_mode="Markdown",
        reply_markup=trip_list_keyboard(trips, lang),
    )


# ── Trip detail / actions callbacks ──────────────────────────────────

async def trip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle trip:view:<id>, trip:pause:<id>, trip:resume:<id>, trip:delete:<id>."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    action = parts[1]
    trip_id = int(parts[2])
    lang = _get_lang(query.from_user.id)
    currency = _get_currency(query.from_user.id)

    with get_session() as session:
        trip = session.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            await query.edit_message_text(t("trip_not_found", lang), parse_mode="Markdown")
            return

        if action == "view":
            latest = (
                session.query(PriceSnapshot)
                .filter(PriceSnapshot.trip_id == trip.id)
                .order_by(PriceSnapshot.timestamp.desc())
                .first()
            )

            if latest:
                price_info = t("latest_price", lang,
                               price=f"{latest.price:.2f}",
                               currency=latest.currency,
                               airline=latest.airline or "—",
                               stopovers=latest.stopovers,
                               duration=f"{latest.duration_minutes // 60}h {latest.duration_minutes % 60:02d}m"
                                        if latest.duration_minutes else "—",
                               link="#")
            else:
                price_info = t("no_prices_yet", lang)

            status = "✅ Active" if trip.active else "⏸ Paused"
            max_price_str = f"{trip.max_price:.2f} {currency}" if trip.max_price else "—"
            direct_str = t("yes", lang) if trip.direct_only else t("no", lang)

            text = t("trip_detail", lang,
                     name=trip.name,
                     origin=trip.origin,
                     destination=trip.destination,
                     date_from=trip.date_from.strftime("%d/%m/%Y"),
                     date_to=trip.date_to.strftime("%d/%m/%Y"),
                     flex_days=trip.flex_days,
                     max_price=max_price_str,
                     direct_only=direct_str,
                     interval=trip.check_interval_hours,
                     status=status,
                     price_info=price_info)

            # Try to send chart
            chart = generate_price_chart(session, trip.id, currency)
            if chart:
                await query.message.reply_photo(photo=chart, caption=text, parse_mode="Markdown")
                await query.delete_message()
            else:
                await query.edit_message_text(
                    text, parse_mode="Markdown",
                    reply_markup=trip_actions_keyboard(trip, lang),
                )

        elif action == "pause":
            trip.active = False
            await query.edit_message_text(
                t("trip_paused", lang, name=trip.name), parse_mode="Markdown"
            )

        elif action == "resume":
            trip.active = True
            await query.edit_message_text(
                t("trip_resumed", lang, name=trip.name), parse_mode="Markdown"
            )

        elif action == "delete":
            await query.edit_message_text(
                t("confirm_delete", lang, name=trip.name),
                parse_mode="Markdown",
                reply_markup=confirm_delete_keyboard(trip.id, lang),
            )

        elif action == "confirmdelete":
            name = trip.name
            session.delete(trip)
            await query.edit_message_text(
                t("trip_deleted", lang, name=name), parse_mode="Markdown"
            )

        elif action == "canceldelete":
            await query.edit_message_text(
                t("trip_paused", lang, name=trip.name).replace("paused", "kept"),
                parse_mode="Markdown",
            )


# ── Registration ─────────────────────────────────────────────────────

def register(app) -> None:
    """Register all trip handlers."""
    # Conversation for /newtrip
    conv = ConversationHandler(
        entry_points=[CommandHandler("newtrip", newtrip_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_name)],
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_origin)],
            DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_dest)],
            DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_dates)],
            FLEX: [MessageHandler(filters.TEXT, trip_flex)],
            PRICE: [MessageHandler(filters.TEXT, trip_price)],
            DIRECT: [CallbackQueryHandler(trip_direct_callback, pattern=r"^yn:")],
            CONFIRM: [CallbackQueryHandler(trip_confirm_callback, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("trips", trips_command))
    app.add_handler(CallbackQueryHandler(trip_callback, pattern=r"^trip:"))
