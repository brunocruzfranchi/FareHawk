"""Spanish strings."""

STRINGS = {
    # /start
    "welcome": (
        "🦅 *¡Bienvenido a FareHawk!*\n\n"
        "Busco las mejores ofertas de vuelos para ti.\n"
        "Configura un viaje y te avisaré cuando bajen los precios.\n\n"
        "Por favor, elige tu idioma:"
    ),
    "language_set": "✅ Idioma configurado: *Español*.",
    "help": (
        "🦅 *Comandos de FareHawk*\n\n"
        "/newtrip — Crear un nuevo viaje para seguir\n"
        "/trips — Listar tus viajes activos\n"
        "/search `<origen> <destino> <DD/MM/AAAA>` — Búsqueda rápida\n"
        "/check — Forzar verificación de precios\n"
        "/edit — Editar un viaje existente\n"
        "/settings — Cambiar idioma o moneda\n"
        "/help — Mostrar esta ayuda"
    ),

    # /newtrip wizard
    "trip_name_ask": "✏️ ¡Vamos a crear un nuevo viaje!\n\n¿Cómo quieres llamarlo? (ej. *Verano en Barcelona*)",
    "trip_origin_ask": "📍 ¿Desde dónde vuelas? (código IATA o ciudad, ej. `MAD` o `Madrid`)",
    "trip_dest_ask": "🎯 ¿A dónde vuelas? (código IATA o ciudad, ej. `BCN` o `Barcelona`)",
    "trip_dates_ask": (
        "📅 ¿Cuál es tu rango de fechas de viaje?\n\n"
        "Envía dos fechas separadas por un espacio:\n"
        "`DD/MM/AAAA DD/MM/AAAA`\n\n"
        "Ejemplo: `01/07/2025 15/07/2025`"
    ),
    "trip_dates_invalid": "❌ Fechas inválidas. Usa el formato `DD/MM/AAAA DD/MM/AAAA`.",
    "trip_flex_ask": "🔄 ¿Cuántos días de flexibilidad (±)? (por defecto: 3)\n\nEnvía un número o /skip para usar el valor por defecto.",
    "trip_price_ask": "💰 ¿Establecer un presupuesto máximo en *{currency}*?\n\nEnvía un número o /skip para omitir.",
    "trip_direct_ask": "✈️ ¿Solo vuelos directos?",
    "trip_confirm": (
        "✅ *Resumen del viaje*\n\n"
        "📝 Nombre: *{name}*\n"
        "📍 De: `{origin}` → `{destination}`\n"
        "📅 Fechas: {date_from} — {date_to} (±{flex_days} días)\n"
        "✈️ Tipo: {flight_type}\n"
        "{return_dates}"
        "💰 Precio máximo: {max_price}\n"
        "✈️ Solo directo: {direct_only}\n\n"
        "¿Guardar este viaje?"
    ),
    "trip_saved": "🎉 ¡Viaje *{name}* guardado! Empezaré a buscar precios para ti.",
    "trip_cancelled": "❌ Creación del viaje cancelada.",

    # /trips
    "no_trips": "No tienes viajes aún. ¡Usa /newtrip para crear uno!",
    "trips_header": "🦅 *Tus Viajes*\n",
    "trip_row": "• *{name}* ({origin}→{destination}) — {status}",

    # /trip detail
    "trip_detail": (
        "📋 *{name}*\n\n"
        "📍 {origin} → {destination}\n"
        "📅 {date_from} — {date_to} (±{flex_days}d)\n"
        "💰 Presupuesto: {max_price}\n"
        "✈️ Solo directo: {direct_only}\n"
        "🔄 Verificar cada {interval}h\n"
        "📊 Estado: {status}\n\n"
        "{price_info}"
    ),
    "latest_price": "💵 Último precio: *{price} {currency}* ({airline}, {stopovers} escala(s), {duration})\n🔗 {link}",
    "no_prices_yet": "Aún no hay datos de precios — ¡la próxima verificación será pronto!",
    "trip_not_found": "❌ Viaje no encontrado.",

    # Actions
    "trip_paused": "⏸ Viaje *{name}* pausado.",
    "trip_resumed": "▶️ Viaje *{name}* reanudado.",
    "trip_deleted": "🗑 Viaje *{name}* eliminado.",
    "confirm_delete": "¿Seguro que quieres eliminar *{name}*?",

    # /search
    "search_usage": "Uso: `/search JFK BCN 01/07/2025 [15/07/2025]`\n\nAgregá una fecha de vuelta para búsquedas de ida y vuelta.",
    "search_searching": "🔍 Buscando vuelos {origin} → {destination} el {date}…",
    "search_no_results": "😕 No se encontraron vuelos para esa ruta/fecha.",
    "search_result": (
        "✈️ *{airline}* — *{price} {currency}*\n"
        "{flight_type}\n"
        "📅 {dates}\n"
        "⏱ {duration} | {stopovers} escala(s)\n"
        "🔗 [Reservar]({link})"
    ),

    # /settings
    "settings_menu": "⚙️ *Configuración*\n\nElige qué cambiar:",
    "select_language": "🌐 Elige idioma:",
    "select_currency": "💱 Elige moneda:",
    "currency_set": "✅ Moneda configurada: *{currency}*.",

    # Alerts
    "alert_price_drop": (
        "🔻 *¡Bajada de precio!* Viaje: *{name}*\n\n"
        "Anterior: {prev_price} {currency}\n"
        "Ahora: *{price} {currency}* (−{pct}%)\n"
        "✈️ {airline} | {stopovers} escala(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Reservar ahora]({link})"
    ),
    "alert_new_low": (
        "🏆 *¡Nuevo mínimo histórico!* Viaje: *{name}*\n\n"
        "Precio: *{price} {currency}*\n"
        "✈️ {airline} | {stopovers} escala(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Reservar ahora]({link})"
    ),
    "alert_threshold": (
        "🎯 *¡Bajo presupuesto!* Viaje: *{name}*\n\n"
        "Presupuesto: {budget} {currency}\n"
        "Precio: *{price} {currency}*\n"
        "✈️ {airline} | {stopovers} escala(s) | {duration}\n"
        "📅 {outbound} → {return_date}\n"
        "🔗 [Reservar ahora]({link})"
    ),

    # Flight type
    "flight_type_ask": "✈️ ¿Ida y vuelta o solo ida?",
    "flight_type_round": "🔄 Ida y vuelta",
    "flight_type_oneway": "➡️ Solo ida",
    "return_dates_ask": (
        "📅 ¿Cuál es tu rango de fechas de *regreso*?\n\n"
        "Envía dos fechas separadas por un espacio:\n"
        "`DD/MM/AAAA DD/MM/AAAA`\n\n"
        "Ejemplo: `15/07/2025 25/07/2025`"
    ),
    "return_dates_invalid": "❌ Fechas de regreso inválidas. Usa el formato `DD/MM/AAAA DD/MM/AAAA`.",
    "flight_type_label_round": "🔄 Ida y vuelta",
    "flight_type_label_oneway": "➡️ Solo ida",

    # /check
    "check_header": "🔍 *Verificación de Precios*\n",
    "check_no_trips": "No hay viajes activos para verificar. ¡Usa /newtrip para crear uno!",
    "check_searching": "🔍 Verificando precios para *{name}* ({origin} → {destination})…",
    "check_no_results": "😕 No se encontraron resultados para *{name}*.",
    "check_result": (
        "💰 *{name}*\n\n"
        "✈️ {airline} — *{price} {currency}*\n"
        "{flight_type}\n"
        "📅 {dates}\n"
        "⏱ {duration} | {stopovers} escala(s)\n"
        "🔗 [Reservar]({link})"
    ),
    "check_complete": "✅ ¡Verificación de precios completa!",
    "check_trip_not_found": "❌ Viaje #{trip_id} no encontrado o no es tuyo.",

    # /edit
    "edit_select_trip": "📝 *Editar un Viaje*\n\nSelecciona un viaje para editar:",
    "edit_no_trips": "No hay viajes para editar. ¡Usa /newtrip para crear uno!",
    "edit_select_field": "¿Qué quieres editar de *{name}*?",
    "edit_field_name": "📝 Nombre",
    "edit_field_origin": "📍 Origen",
    "edit_field_destination": "🎯 Destino",
    "edit_field_dates": "📅 Fechas",
    "edit_field_flex": "🔄 Días de flexibilidad",
    "edit_field_max_price": "💰 Precio máximo",
    "edit_field_direct": "✈️ Solo directo",
    "edit_field_flight_type": "🔄 Tipo de vuelo",
    "edit_send_value": "Envía el nuevo valor para *{field}*:",
    "edit_send_dates": "Envía las nuevas fechas (DD/MM/AAAA DD/MM/AAAA):",
    "edit_saved": "✅ *{field}* actualizado a: {value}",
    "edit_invalid": "❌ Valor inválido. Por favor intenta de nuevo.",
    "edit_cancelled": "❌ Edición cancelada.",

    # Weekly digest
    "digest_header": "📊 *Resumen Semanal de Vuelos*\n\n",
    "digest_trip": (
        "🦅 *{name}* ({origin} → {destination})\n"
        "   💰 Mejor precio: *{price} {currency}*\n"
        "   {trend} Cambio: {change}\n\n"
    ),
    "digest_no_data": (
        "🦅 *{name}* ({origin} → {destination})\n"
        "   Sin datos de precio aún\n\n"
    ),
    "digest_footer": "¡Que tengas una gran semana! ✈️",
    "digest_no_trips": "No hay viajes activos para reportar.",
    "trend_up": "📈",
    "trend_down": "📉",
    "trend_stable": "➡️",

    # Misc
    "yes": "Sí",
    "no": "No",
    "cancel": "Cancelar",
    "save": "Guardar",
    "skip": "Omitir",
    "back": "Volver",
    "error": "⚠️ Algo salió mal. Por favor, inténtalo de nuevo más tarde.",
    "btn_view": "Ver",
    "btn_pause": "⏸ Pausar",
    "btn_resume": "▶️ Reanudar",
    "btn_delete": "🗑 Eliminar",
}
