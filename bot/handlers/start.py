"""Handlers for /start, /help, and language selection."""

import logging

from telegram import Update
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from bot.i18n import t
from bot.keyboards.inline import language_keyboard
from core.database import get_or_create_user, get_session
from core.models import User

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome message and language selection."""
    tg_user = update.effective_user
    user = get_or_create_user(tg_user.id, tg_user.username)
    lang = user.language

    await update.message.reply_text(
        t("welcome", lang),
        parse_mode="Markdown",
        reply_markup=language_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show available commands."""
    tg_user = update.effective_user
    user = get_or_create_user(tg_user.id, tg_user.username)
    lang = user.language

    await update.message.reply_text(t("help", lang), parse_mode="Markdown")


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection inline button (lang:en / lang:es)."""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split(":")[1]  # "en" or "es"

    with get_session() as session:
        user = session.query(User).filter(User.telegram_id == query.from_user.id).first()
        if user:
            user.language = lang_code

    await query.edit_message_text(
        t("language_set", lang_code) + "\n\n" + t("help", lang_code),
        parse_mode="Markdown",
    )


def register(app) -> None:
    """Register start/help handlers on the Application."""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang:"))
