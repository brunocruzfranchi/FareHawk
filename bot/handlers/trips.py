"""Handlers for trip CRUD: /newtrip wizard, /trips, /trip, /edit, pause, resume, delete."""

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
    flight_type_keyboard,
    edit_field_keyboard,
)
from core.database import get_or_create_user, get_session
from core.models import User, Trip, PriceSnapshot
from services.charts import generate_price_chart

logger = logging.getLogger(__name__)


async def _safe_edit_or_reply(query, text: str, parse_mode: str = "Markdown", reply_markup=None):
    """Edit message text/caption, or send new message if the original is a photo."""
    try:
        if query.message and query.message.photo:
            # It's a photo message — edit caption or send new + delete
            try:
                kwargs = {"caption": text, "parse_mode": parse_mode}
                if reply_markup:
                    kwargs["reply_markup"] = reply_markup
                await query.edit_message_caption(**kwargs)
            except Exception:
                # Caption too long or other issue — send new message
                await query.message.reply_text(
                    text, parse_mode=parse_mode, reply_markup=reply_markup
                )
                try:
                    await query.message.delete()
                except Exception:
                    pass
        else:
            kwargs = {"text": text, "parse_mode": parse_mode}
            if reply_markup:
                kwargs["reply_markup"] = reply_markup
            await query.edit_message_text(**kwargs)
    except Exception:
        # Last resort — just send a new message
        await query.message.reply_text(
            text, parse_mode=parse_mode, reply_markup=reply_markup
        )


# Conversation states for /newtrip
NAME, ORIGIN, DEST, DATES, FLIGHT_TYPE, RETURN_DATES, FLEX, PRICE, DIRECT, CONFIRM = range(10)

# Conversation states for /edit
EDIT_SELECT_TRIP, EDIT_SELECT_FIELD, EDIT_VALUE = range(100, 103)


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

    # Ask flight type
    await update.message.reply_text(
        t("flight_type_ask", lang),
        parse_mode="Markdown",
        reply_markup=flight_type_keyboard(lang),
    )
    return FLIGHT_TYPE


async def trip_flight_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)

    flight_type = "round" if query.data == "ftype:round" else "oneway"
    context.user_data["trip"]["flight_type"] = flight_type

    if flight_type == "round":
        await query.edit_message_text(t("return_dates_ask", lang), parse_mode="Markdown")
        return RETURN_DATES
    else:
        context.user_data["trip"]["return_date_from"] = None
        context.user_data["trip"]["return_date_to"] = None
        await query.edit_message_text(t("trip_flex_ask", lang), parse_mode="Markdown")
        return FLEX


async def trip_return_dates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) != 2:
        await update.message.reply_text(t("return_dates_invalid", lang), parse_mode="Markdown")
        return RETURN_DATES

    try:
        rdf = datetime.strptime(parts[0], "%d/%m/%Y").date()
        rdt = datetime.strptime(parts[1], "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text(t("return_dates_invalid", lang), parse_mode="Markdown")
        return RETURN_DATES

    context.user_data["trip"]["return_date_from"] = rdf
    context.user_data["trip"]["return_date_to"] = rdt
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

    flight_type = td.get("flight_type", "round")
    flight_type_str = t("flight_type_label_round", lang) if flight_type == "round" else t("flight_type_label_oneway", lang)

    return_dates_str = ""
    if flight_type == "round" and td.get("return_date_from") and td.get("return_date_to"):
        return_dates_str = f"📅 Return: {td['return_date_from'].strftime('%d/%m/%Y')} — {td['return_date_to'].strftime('%d/%m/%Y')}\n"

    await query.edit_message_text(
        t("trip_confirm", lang,
          name=td["name"],
          origin=td["origin"],
          destination=td["destination"],
          date_from=td["date_from"].strftime("%d/%m/%Y"),
          date_to=td["date_to"].strftime("%d/%m/%Y"),
          flex_days=td["flex_days"],
          max_price=max_price_str,
          direct_only=direct_str,
          flight_type=flight_type_str,
          return_dates=return_dates_str),
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
            flight_type=td.get("flight_type", "round"),
            return_date_from=td.get("return_date_from"),
            return_date_to=td.get("return_date_to"),
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
    context.user_data.pop("edit", None)
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
            await _safe_edit_or_reply(query, t("trip_not_found", lang))
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

            # Flight type info
            flight_type = getattr(trip, "flight_type", "round") or "round"
            flight_type_str = t("flight_type_label_round", lang) if flight_type == "round" else t("flight_type_label_oneway", lang)
            return_dates_str = ""
            rdf = getattr(trip, "return_date_from", None)
            rdt = getattr(trip, "return_date_to", None)
            if flight_type == "round" and rdf and rdt:
                return_dates_str = f"\n📅 Return: {rdf.strftime('%d/%m/%Y')} — {rdt.strftime('%d/%m/%Y')}"

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

            # Append flight type and return dates
            text += f"\n✈️ Type: {flight_type_str}{return_dates_str}"

            # Try to send chart
            chart = generate_price_chart(session, trip.id, currency)
            if chart:
                await query.message.reply_photo(
                    photo=chart, caption=text, parse_mode="Markdown",
                    reply_markup=trip_actions_keyboard(trip, lang),
                )
                await query.delete_message()
            else:
                await _safe_edit_or_reply(
                    query, text,
                    reply_markup=trip_actions_keyboard(trip, lang),
                )

        elif action == "pause":
            trip.active = False
            await _safe_edit_or_reply(query, t("trip_paused", lang, name=trip.name))

        elif action == "resume":
            trip.active = True
            await _safe_edit_or_reply(query, t("trip_resumed", lang, name=trip.name))

        elif action == "delete":
            await _safe_edit_or_reply(
                query,
                t("confirm_delete", lang, name=trip.name),
                reply_markup=confirm_delete_keyboard(trip.id, lang),
            )

        elif action == "confirmdelete":
            name = trip.name
            session.delete(trip)
            await _safe_edit_or_reply(query, t("trip_deleted", lang, name=name))

        elif action == "canceldelete":
            await _safe_edit_or_reply(
                query, t("trip_paused", lang, name=trip.name).replace("paused", "kept")
            )


# ── /edit Command ────────────────────────────────────────────────────

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /edit — show list of trips to edit."""
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    lang = user.language

    with get_session() as session:
        trips = session.query(Trip).filter(Trip.user_id == user.id).all()
        if not trips:
            await update.message.reply_text(t("edit_no_trips", lang), parse_mode="Markdown")
            return ConversationHandler.END
        session.expunge_all()

    from bot.keyboards.inline import edit_trip_list_keyboard
    await update.message.reply_text(
        t("edit_select_trip", lang),
        parse_mode="Markdown",
        reply_markup=edit_trip_list_keyboard(trips, lang),
    )
    return EDIT_SELECT_TRIP


async def edit_select_trip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User selected a trip to edit."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)

    trip_id = int(query.data.split(":")[1])
    context.user_data["edit"] = {"trip_id": trip_id}

    with get_session() as session:
        trip = session.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            await query.edit_message_text(t("trip_not_found", lang), parse_mode="Markdown")
            return ConversationHandler.END
        trip_name = trip.name

    await query.edit_message_text(
        t("edit_select_field", lang, name=trip_name),
        parse_mode="Markdown",
        reply_markup=edit_field_keyboard(trip_id, lang),
    )
    return EDIT_SELECT_FIELD


async def edit_select_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User selected a field to edit."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)

    # editfield:<trip_id>:<field>
    parts = query.data.split(":")
    trip_id = int(parts[1])
    field = parts[2]

    context.user_data["edit"] = {"trip_id": trip_id, "field": field}

    # For direct_only and flight_type, show inline keyboard instead of text input
    if field == "direct":
        await query.edit_message_text(
            t("trip_direct_ask", lang),
            parse_mode="Markdown",
            reply_markup=yes_no_keyboard(lang),
        )
        return EDIT_VALUE
    elif field == "flight_type":
        await query.edit_message_text(
            t("flight_type_ask", lang),
            parse_mode="Markdown",
            reply_markup=flight_type_keyboard(lang),
        )
        return EDIT_VALUE
    elif field == "dates":
        await query.edit_message_text(
            t("edit_send_dates", lang),
            parse_mode="Markdown",
        )
        return EDIT_VALUE
    else:
        field_label = t(f"edit_field_{field}", lang)
        await query.edit_message_text(
            t("edit_send_value", lang, field=field_label),
            parse_mode="Markdown",
        )
        return EDIT_VALUE


async def edit_value_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for edit value."""
    lang = _get_lang(update.effective_user.id)
    edit_data = context.user_data.get("edit", {})
    trip_id = edit_data.get("trip_id")
    field = edit_data.get("field")

    if not trip_id or not field:
        await update.message.reply_text(t("edit_cancelled", lang), parse_mode="Markdown")
        return ConversationHandler.END

    text = update.message.text.strip()
    value = None
    display_value = text

    try:
        if field == "name":
            value = text
        elif field == "origin":
            value = text.upper()
            display_value = value
        elif field == "destination":
            value = text.upper()
            display_value = value
        elif field == "dates":
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("Need two dates")
            df = datetime.strptime(parts[0], "%d/%m/%Y").date()
            dt = datetime.strptime(parts[1], "%d/%m/%Y").date()
            # Will set both below
            with get_session() as session:
                trip = session.query(Trip).filter(Trip.id == trip_id).first()
                if trip:
                    trip.date_from = df
                    trip.date_to = dt
            field_label = t("edit_field_dates", lang)
            await update.message.reply_text(
                t("edit_saved", lang, field=field_label, value=f"{parts[0]} — {parts[1]}"),
                parse_mode="Markdown",
            )
            context.user_data.pop("edit", None)
            return ConversationHandler.END
        elif field == "flex":
            value = int(text)
            display_value = str(value)
        elif field == "max_price":
            if text.lower() in ("none", "0", "-", "/skip"):
                value = None
                display_value = "—"
            else:
                value = float(text)
                display_value = f"{value:.2f}"
        else:
            await update.message.reply_text(t("edit_invalid", lang), parse_mode="Markdown")
            return ConversationHandler.END
    except (ValueError, TypeError):
        await update.message.reply_text(t("edit_invalid", lang), parse_mode="Markdown")
        return EDIT_VALUE

    # Apply the edit
    field_map = {
        "name": "name",
        "origin": "origin",
        "destination": "destination",
        "flex": "flex_days",
        "max_price": "max_price",
    }

    db_field = field_map.get(field)
    if db_field:
        with get_session() as session:
            trip = session.query(Trip).filter(Trip.id == trip_id).first()
            if trip:
                setattr(trip, db_field, value)

    field_label = t(f"edit_field_{field}", lang)
    await update.message.reply_text(
        t("edit_saved", lang, field=field_label, value=display_value),
        parse_mode="Markdown",
    )
    context.user_data.pop("edit", None)
    return ConversationHandler.END


async def edit_value_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle callback for direct_only and flight_type edits."""
    query = update.callback_query
    await query.answer()
    lang = _get_lang(query.from_user.id)
    edit_data = context.user_data.get("edit", {})
    trip_id = edit_data.get("trip_id")
    field = edit_data.get("field")

    if not trip_id or not field:
        await query.edit_message_text(t("edit_cancelled", lang), parse_mode="Markdown")
        return ConversationHandler.END

    if field == "direct":
        value = query.data == "yn:yes"
        display_value = t("yes", lang) if value else t("no", lang)
        with get_session() as session:
            trip = session.query(Trip).filter(Trip.id == trip_id).first()
            if trip:
                trip.direct_only = value

    elif field == "flight_type":
        value = "round" if query.data == "ftype:round" else "oneway"
        display_value = t(f"flight_type_label_{value}", lang)
        with get_session() as session:
            trip = session.query(Trip).filter(Trip.id == trip_id).first()
            if trip:
                trip.flight_type = value

    else:
        await query.edit_message_text(t("edit_cancelled", lang), parse_mode="Markdown")
        context.user_data.pop("edit", None)
        return ConversationHandler.END

    field_label = t(f"edit_field_{field}", lang)
    await query.edit_message_text(
        t("edit_saved", lang, field=field_label, value=display_value),
        parse_mode="Markdown",
    )
    context.user_data.pop("edit", None)
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = _get_lang(update.effective_user.id)
    context.user_data.pop("edit", None)
    await update.message.reply_text(t("edit_cancelled", lang), parse_mode="Markdown")
    return ConversationHandler.END


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
            FLIGHT_TYPE: [CallbackQueryHandler(trip_flight_type_callback, pattern=r"^ftype:")],
            RETURN_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, trip_return_dates)],
            FLEX: [MessageHandler(filters.TEXT, trip_flex)],
            PRICE: [MessageHandler(filters.TEXT, trip_price)],
            DIRECT: [CallbackQueryHandler(trip_direct_callback, pattern=r"^yn:")],
            CONFIRM: [CallbackQueryHandler(trip_confirm_callback, pattern=r"^confirm:")],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    app.add_handler(conv)

    # Conversation for /edit
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            EDIT_SELECT_TRIP: [CallbackQueryHandler(edit_select_trip_callback, pattern=r"^edtrip:")],
            EDIT_SELECT_FIELD: [CallbackQueryHandler(edit_select_field_callback, pattern=r"^editfield:")],
            EDIT_VALUE: [
                CallbackQueryHandler(edit_value_callback, pattern=r"^(yn:|ftype:)"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
    )
    app.add_handler(edit_conv)

    app.add_handler(CommandHandler("trips", trips_command))
    app.add_handler(CallbackQueryHandler(trip_callback, pattern=r"^trip:"))
