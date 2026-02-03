"""Internationalization helpers."""

from bot.i18n.en import STRINGS as EN
from bot.i18n.es import STRINGS as ES

_LANGUAGES = {"en": EN, "es": ES}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translate *key* into the given language, with optional format kwargs."""
    strings = _LANGUAGES.get(lang, EN)
    template = strings.get(key, EN.get(key, key))  # fallback → English → raw key
    try:
        return template.format(**kwargs) if kwargs else template
    except (KeyError, IndexError):
        return template
