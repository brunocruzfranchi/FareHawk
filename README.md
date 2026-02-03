# 🦅 FareHawk — Flight Deal Hunting Telegram Bot

FareHawk monitors flight prices and alerts you when deals drop. Set up trips you're interested in and let the hawk do the hunting.

## Features

- **Trip Tracking** — Create trips with origin, destination, dates, and budget
- **Price Monitoring** — Automatic checks every 3 hours via Kiwi/Tequila API
- **Smart Alerts** — Notifies you on:
  - Price drops > 10%
  - New all-time low prices
  - Prices under your budget threshold
- **Price Charts** — Visual price history with matplotlib
- **Multi-language** — English 🇬🇧 and Spanish 🇪🇸
- **Multi-currency** — USD, EUR, GBP, CAD, AUD, MXN, COP, BRL

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome & language selection |
| `/newtrip` | Create a new trip (guided wizard) |
| `/trips` | List your active trips |
| `/search JFK BCN 01/07/2025` | Quick one-off flight search |
| `/settings` | Change language or currency |
| `/help` | Show available commands |

## Quick Start

### 1. Prerequisites

- Python 3.12+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Kiwi/Tequila API key (from [tequila.kiwi.com](https://tequila.kiwi.com/))

### 2. Clone & Configure

```bash
git clone <your-repo-url>
cd farehawk
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
TELEGRAM_BOT_TOKEN=your-bot-token-here
KIWI_API_KEY=your-kiwi-api-key-here
```

### 3a. Run with Docker (Recommended)

```bash
docker-compose up -d --build
```

View logs:

```bash
docker-compose logs -f farehawk
```

### 3b. Run Locally

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set PYTHONPATH so imports resolve
export PYTHONPATH=$(pwd)

python bot/main.py
```

## Project Structure

```
farehawk/
├── bot/                    # Telegram bot layer
│   ├── main.py             # Entry point
│   ├── handlers/           # Command & callback handlers
│   │   ├── start.py        # /start, /help, language selection
│   │   ├── trips.py        # /newtrip wizard, /trips, /trip actions
│   │   ├── search.py       # /search quick one-off
│   │   └── settings.py     # /settings (currency, language)
│   ├── keyboards/          # Inline keyboard builders
│   └── i18n/               # Internationalization (en, es)
├── core/                   # Core infrastructure
│   ├── models.py           # SQLAlchemy models
│   ├── database.py         # DB engine & sessions
│   ├── scheduler.py        # APScheduler setup
│   └── config.py           # Env-based configuration
├── providers/              # Flight data providers
│   ├── base.py             # Abstract provider + FlightResult
│   ├── kiwi.py             # Kiwi/Tequila API
│   ├── amadeus.py          # Amadeus (Phase 2 stub)
│   └── aggregator.py       # Multi-source aggregation
├── services/               # Business logic
│   ├── price_checker.py    # Periodic check runner
│   ├── alerts.py           # Alert evaluation engine
│   └── charts.py           # Price history charts
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Data Models

- **User** — Telegram user with language & currency preferences
- **Trip** — Tracked route with dates, budget, and check interval
- **PriceSnapshot** — Historical price data point for a trip
- **Alert** — Triggered notification record

## Adding a New Language

1. Create `bot/i18n/<code>.py` with a `STRINGS` dict (copy `en.py` as template)
2. Register it in `bot/i18n/__init__.py`
3. Add a button in `bot/keyboards/inline.py` → `language_keyboard()`

## Adding a New Provider

1. Create `providers/<name>.py` implementing `FlightProvider`
2. Add it to `FlightAggregator.__init__()` in `providers/aggregator.py`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Bot token from BotFather |
| `KIWI_API_KEY` | ✅ | — | Kiwi Tequila API key |
| `AMADEUS_API_KEY` | ❌ | — | Amadeus API key (Phase 2) |
| `AMADEUS_API_SECRET` | ❌ | — | Amadeus API secret (Phase 2) |
| `DATABASE_URL` | ❌ | `sqlite:///data/farehawk.db` | SQLAlchemy database URL |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |

## License

MIT
