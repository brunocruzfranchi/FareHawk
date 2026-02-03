"""Inline keyboard builders for FareHawk bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.i18n import t


# ── Language selection ────────────────────────────────────────────────

def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang:es"),
        ]
    ])


# ── Trip wizard ───────────────────────────────────────────────────────

def yes_no_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("yes", lang), callback_data="yn:yes"),
            InlineKeyboardButton(t("no", lang), callback_data="yn:no"),
        ]
    ])


def confirm_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"✅ {t('save', lang)}", callback_data="confirm:save"),
            InlineKeyboardButton(f"❌ {t('cancel', lang)}", callback_data="confirm:cancel"),
        ]
    ])


# ── Trip list / actions ──────────────────────────────────────────────

def trip_list_keyboard(trips: list, lang: str = "en") -> InlineKeyboardMarkup:
    """One button per trip to view details."""
    buttons = []
    for trip in trips:
        status = "✅" if trip.active else "⏸"
        buttons.append([
            InlineKeyboardButton(
                f"{status} {trip.name} ({trip.origin}→{trip.destination})",
                callback_data=f"trip:view:{trip.id}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def trip_actions_keyboard(trip, lang: str = "en") -> InlineKeyboardMarkup:
    """Action buttons for a single trip."""
    row = []
    if trip.active:
        row.append(InlineKeyboardButton(t("btn_pause", lang), callback_data=f"trip:pause:{trip.id}"))
    else:
        row.append(InlineKeyboardButton(t("btn_resume", lang), callback_data=f"trip:resume:{trip.id}"))
    row.append(InlineKeyboardButton(t("btn_delete", lang), callback_data=f"trip:delete:{trip.id}"))
    return InlineKeyboardMarkup([row])


def confirm_delete_keyboard(trip_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"✅ {t('yes', lang)}", callback_data=f"trip:confirmdelete:{trip_id}"),
            InlineKeyboardButton(f"❌ {t('no', lang)}", callback_data=f"trip:canceldelete:{trip_id}"),
        ]
    ])


# ── Settings ──────────────────────────────────────────────────────────

def settings_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 " + t("select_language", lang), callback_data="settings:language")],
        [InlineKeyboardButton("💱 " + t("select_currency", lang), callback_data="settings:currency")],
    ])


def currency_keyboard() -> InlineKeyboardMarkup:
    currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "MXN", "COP", "BRL"]
    rows = []
    for i in range(0, len(currencies), 4):
        row = [
            InlineKeyboardButton(c, callback_data=f"currency:{c}")
            for c in currencies[i:i + 4]
        ]
        rows.append(row)
    return InlineKeyboardMarkup(rows)
