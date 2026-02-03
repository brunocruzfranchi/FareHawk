"""Handler for /settings — language and currency preferences."""

import logging

from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from bot.i18n import t
from bot.keyboards.inline import settings_keyboard, language_keyboard, currency_keyboard
from core.database import get_or_create_user, get_session
from core.models import User

logger = logging.getLogger(__name__)


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings — show settings menu."""
    user = get_or_create_user(update.effective_user.id, update.effective_user.username)
    lang = user.language

    await update.message.reply_text(
        t("settings_menu", lang),
        parse_mode="Markdown",
        reply_markup=settings_keyboard(lang),
    )


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings inline buttons."""
    query = update.callback_query
    await query.answer()

    data = query.data  # settings:language / settings:currency
    user = get_or_create_user(query.from_user.id, query.from_user.username)
    lang = user.language

    if data == "settings:language":
        await query.edit_message_text(
            t("select_language", lang),
            parse_mode="Markdown",
            reply_markup=language_keyboard(),
        )
    elif data == "settings:currency":
        await query.edit_message_text(
            t("select_currency", lang),
            parse_mode="Markdown",
            reply_markup=currency_keyboard(),
        )


async def currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle currency selection."""
    query = update.callback_query
    await query.answer()

    currency_code = query.data.split(":")[1]  # e.g. "USD"

    with get_session() as session:
        user = session.query(User).filter(User.telegram_id == query.from_user.id).first()
        if user:
            user.currency = currency_code
            lang = user.language
        else:
            lang = "en"

    await query.edit_message_text(
        t("currency_set", lang, currency=currency_code),
        parse_mode="Markdown",
    )


def register(app) -> None:
    """Register settings handlers."""
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings:"))
    app.add_handler(CallbackQueryHandler(currency_callback, pattern=r"^currency:"))
