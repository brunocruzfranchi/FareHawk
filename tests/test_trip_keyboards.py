from datetime import date

from bot.keyboards.inline import trip_actions_keyboard
from core.models import Trip


def _trip(*, active=True):
    return Trip(
        id=42,
        name="Barcelona",
        origin="JFK",
        destination="BCN",
        date_from=date(2026, 10, 17),
        date_to=date(2026, 10, 17),
        active=active,
    )


def _button_payloads(markup):
    return [button.callback_data or button.url for row in markup.inline_keyboard for button in row]


def test_trip_actions_keyboard_exposes_primary_trip_actions():
    payloads = _button_payloads(trip_actions_keyboard(_trip(), "en"))

    assert "trip:chart:42" in payloads
    assert "edtrip:42" in payloads
    assert "trip:pause:42" in payloads
    assert "trip:delete:42" in payloads
    assert any(payload.startswith("https://www.google.com/travel/flights") for payload in payloads)


def test_trip_actions_keyboard_uses_resume_for_paused_trips():
    payloads = _button_payloads(trip_actions_keyboard(_trip(active=False), "en"))

    assert "trip:resume:42" in payloads
    assert "trip:pause:42" not in payloads
