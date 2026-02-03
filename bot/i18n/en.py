"""English strings."""

STRINGS = {
    # /start
    "welcome": (
        "🦅 *Welcome to FareHawk!*\n\n"
        "I hunt the best flight deals for you.\n"
        "Set up a trip and I'll alert you when prices drop.\n\n"
        "Please choose your language:"
    ),
    "language_set": "✅ Language set to *English*.",
    "help": (
        "🦅 *FareHawk Commands*\n\n"
        "/newtrip — Create a new trip to watch\n"
        "/trips — List your active trips\n"
        "/search `<origin> <dest> <DD/MM/YYYY>` — Quick one-off search\n"
        "/settings — Change language or currency\n"
        "/help — Show this help message"
    ),

    # /newtrip wizard
    "trip_name_ask": "✏️ Let's create a new trip!\n\nWhat would you like to call it? (e.g. *Summer in Barcelona*)",
    "trip_origin_ask": "📍 Where are you flying *from*? (IATA code or city, e.g. `JFK` or `New York`)",
    "trip_dest_ask": "🎯 Where are you flying *to*? (IATA code or city, e.g. `BCN` or `Barcelona`)",
    "trip_dates_ask": (
        "📅 What is your travel date range?\n\n"
        "Send two dates separated by a space:\n"
        "`DD/MM/YYYY DD/MM/YYYY`\n\n"
        "Example: `01/07/2025 15/07/2025`"
    ),
    "trip_dates_invalid": "❌ Invalid dates. Please use `DD/MM/YYYY DD/MM/YYYY` format.",
    "trip_flex_ask": "🔄 How many flex days (±)? (default: 3)\n\nSend a number or /skip to use the default.",
    "trip_price_ask": "💰 Set a maximum price budget in *{currency}*?\n\nSend a number or /skip to skip.",
    "trip_direct_ask": "✈️ Direct flights only?",
    "trip_confirm": (
        "✅ *Trip Summary*\n\n"
        "📝 Name: *{name}*\n"
        "📍 From: `{origin}` → `{destination}`\n"
        "📅 Dates: {date_from} — {date_to} (±{flex_days} days)\n"
        "💰 Max price: {max_price}\n"
        "✈️ Direct only: {direct_only}\n\n"
        "Save this trip?"
    ),
    "trip_saved": "🎉 Trip *{name}* saved! I'll start checking prices for you.",
    "trip_cancelled": "❌ Trip creation cancelled.",

    # /trips
    "no_trips": "You don't have any trips yet. Use /newtrip to create one!",
    "trips_header": "🦅 *Your Trips*\n",
    "trip_row": "• *{name}* ({origin}→{destination}) — {status}",

    # /trip detail
    "trip_detail": (
        "📋 *{name}*\n\n"
        "📍 {origin} → {destination}\n"
        "📅 {date_from} — {date_to} (±{flex_days}d)\n"
        "💰 Budget: {max_price}\n"
        "✈️ Direct only: {direct_only}\n"
        "🔄 Check every {interval}h\n"
        "📊 Status: {status}\n\n"
        "{price_info}"
    ),
    "latest_price": "💵 Latest price: *{price} {currency}* ({airline}, {stopovers} stop(s), {duration})\n🔗 {link}",
    "no_prices_yet": "No price data yet — next check coming soon!",
    "trip_not_found": "❌ Trip not found.",

    # Actions
    "trip_paused": "⏸ Trip *{name}* paused.",
    "trip_resumed": "▶️ Trip *{name}* resumed.",
    "trip_deleted": "🗑 Trip *{name}* deleted.",
    "confirm_delete": "Are you sure you want to delete *{name}*?",

    # /search
    "search_usage": "Usage: `/search JFK BCN 01/07/2025`",
    "search_searching": "🔍 Searching flights {origin} → {destination} on {date}…",
    "search_no_results": "😕 No flights found for that route/date.",
    "search_result": (
        "✈️ *{airline}* — *{price} {currency}*\n"
        "📅 {outbound_date}\n"
        "⏱ {duration} | {stopovers} stop(s)\n"
        "🔗 [Book]({link})"
    ),

    # /settings
    "settings_menu": "⚙️ *Settings*\n\nChoose what to change:",
    "select_language": "🌐 Choose language:",
    "select_currency": "💱 Choose currency:",
    "currency_set": "✅ Currency set to *{currency}*.",

    # Alerts
    "alert_price_drop": (
        "🔻 *Price Drop!* Trip: *{name}*\n\n"
        "Previous: {prev_price} {currency}\n"
        "Now: *{price} {currency}* (−{pct}%)\n"
        "✈️ {airline} | {stopovers} stop(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Book now]({link})"
    ),
    "alert_new_low": (
        "🏆 *New All-Time Low!* Trip: *{name}*\n\n"
        "Price: *{price} {currency}*\n"
        "✈️ {airline} | {stopovers} stop(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Book now]({link})"
    ),
    "alert_threshold": (
        "🎯 *Under Budget!* Trip: *{name}*\n\n"
        "Budget: {budget} {currency}\n"
        "Price: *{price} {currency}*\n"
        "✈️ {airline} | {stopovers} stop(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Book now]({link})"
    ),

    # Misc
    "yes": "Yes",
    "no": "No",
    "cancel": "Cancel",
    "save": "Save",
    "skip": "Skip",
    "back": "Back",
    "error": "⚠️ Something went wrong. Please try again later.",
    "btn_view": "View",
    "btn_pause": "⏸ Pause",
    "btn_resume": "▶️ Resume",
    "btn_delete": "🗑 Delete",
}
