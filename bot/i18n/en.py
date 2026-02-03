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
        "/check — Force an immediate price check\n"
        "/edit — Edit an existing trip\n"
        "/settings — Change language or currency\n"
        "/help — Show this help message"
    ),

    # /newtrip wizard
    "trip_name_ask": "✏️ Let's create a new trip!\n\nWhat would you like to call it? (e.g. *Summer in Barcelona*)",
    "trip_origin_ask": "📍 Where are you flying *from*? (IATA code or city, e.g. `JFK` or `New York`)",
    "trip_dest_ask": "🎯 Where are you flying *to*? (IATA code or city, e.g. `BCN` or `Barcelona`)",
    "trip_departure_date_ask": "📅 What is your *departure* date?\n\nSend one date: `DD/MM/YYYY`\n\nExample: `17/10/2026`",
    "trip_return_date_ask": "📅 What is your *return* date?\n\nSend one date: `DD/MM/YYYY`\n\nExample: `01/11/2026`",
    "trip_date_invalid": "❌ Invalid date. Please use `DD/MM/YYYY` format.",
    "trip_flex_ask": "🔄 How many *flex days* (±)? This applies to both departure and return dates. (default: 3)\n\nSend a number or /skip to use the default.",
    "trip_price_ask": "💰 Set a maximum price budget in *{currency}*?\n\nSend a number or /skip to skip.",
    "trip_direct_ask": "✈️ Direct flights only?",
    "trip_confirm": (
        "✅ *Trip Summary*\n\n"
        "📝 Name: *{name}*\n"
        "📍 From: `{origin}` → `{destination}`\n"
        "📅 Departure: {departure_date} (±{flex_days}d)\n"
        "✈️ Type: {flight_type}\n"
        "{return_dates}"
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
        "📅 Departure: {departure_date} (±{flex_days}d)\n"
        "{return_info}"
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
    "search_usage": "Usage: `/search JFK BCN 01/07/2025 [15/07/2025]`\n\nAdd a return date for round trip searches.",
    "search_searching": "🔍 Searching flights {origin} → {destination} on {date}…",
    "search_no_results": "😕 No flights found for that route/date.",
    "search_result": (
        "✈️ *{airline}* — *{price} {currency}*\n"
        "{flight_type}\n"
        "📅 {dates}\n"
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

    # Flight type
    "flight_type_ask": "✈️ Round trip or one-way?",
    "flight_type_round": "🔄 Round trip",
    "flight_type_oneway": "➡️ One-way",
    "return_dates_ask": "📅 What is your *return* date?\n\nSend one date: `DD/MM/YYYY`",
    "return_dates_invalid": "❌ Invalid return date. Please use `DD/MM/YYYY` format.",
    "flight_type_label_round": "🔄 Round trip",
    "flight_type_label_oneway": "➡️ One-way",

    # /check
    "check_header": "🔍 *Force Price Check*\n",
    "check_no_trips": "No active trips to check. Use /newtrip to create one!",
    "check_searching": "🔍 Checking prices for *{name}* ({origin} → {destination})…",
    "check_no_results": "😕 No results found for *{name}*.",
    "check_result": (
        "💰 *{name}*\n\n"
        "✈️ {airline} — *{price} {currency}*\n"
        "{flight_type}\n"
        "📅 {dates}\n"
        "⏱ {duration} | {stopovers} stop(s)\n"
        "🔗 [Book]({link})"
    ),
    "check_complete": "✅ Price check complete!",
    "check_trip_not_found": "❌ Trip #{trip_id} not found or not yours.",

    # /edit
    "edit_select_trip": "📝 *Edit a Trip*\n\nSelect a trip to edit:",
    "edit_no_trips": "No trips to edit. Use /newtrip to create one!",
    "edit_select_field": "What would you like to edit for *{name}*?",
    "edit_field_name": "📝 Name",
    "edit_field_origin": "📍 Origin",
    "edit_field_destination": "🎯 Destination",
    "edit_field_dates": "📅 Dates",
    "edit_field_flex": "🔄 Flex days",
    "edit_field_max_price": "💰 Max price",
    "edit_field_direct": "✈️ Direct only",
    "edit_field_flight_type": "🔄 Flight type",
    "edit_send_value": "Send the new value for *{field}*:",
    "edit_send_dates": "Send new dates (DD/MM/YYYY DD/MM/YYYY):",
    "edit_saved": "✅ *{field}* updated to: {value}",
    "edit_invalid": "❌ Invalid value. Please try again.",
    "edit_cancelled": "❌ Edit cancelled.",

    # Weekly digest
    "digest_header": "📊 *Weekly Flight Digest*\n\n",
    "digest_trip": (
        "🦅 *{name}* ({origin} → {destination})\n"
        "   💰 Best price: *{price} {currency}*\n"
        "   {trend} Change: {change}\n\n"
    ),
    "digest_no_data": (
        "🦅 *{name}* ({origin} → {destination})\n"
        "   No price data yet\n\n"
    ),
    "digest_footer": "Have a great week! ✈️",
    "digest_no_trips": "No active trips to report on.",
    "trend_up": "📈",
    "trend_down": "📉",
    "trend_stable": "➡️",

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
