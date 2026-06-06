# FareHawk

FareHawk is a Telegram bot for tracking flight prices. Users create watched trips with routes, dates, flexibility, currency, and budget preferences; the bot checks configured flight providers on a schedule and sends alerts when prices improve.

## Features

- Trip tracking for one-way and round-trip flights
- Scheduled price checks every 3 hours by default
- Manual checks with `/check`
- One-off searches with `/search`
- Price-drop, new all-time-low, and budget-threshold alerts
- Price history snapshots and chart generation
- English and Spanish bot copy
- Multi-currency searches: USD, EUR, GBP, CAD, AUD, MXN, COP, BRL
- Docker and local Python runtime support

## Flight Providers

FareHawk can query any provider configured in `.env`. For open-source usage, providers are intentionally classified by setup friction and data-source risk:

| Provider | Tier | Environment variable(s) | Recommendation | Notes |
|----------|------|--------------------------|----------------|-------|
| Amadeus Self-Service | Official | `AMADEUS_API_KEY`, `AMADEUS_API_SECRET`, optional `AMADEUS_ENV` | Recommended default | Official self-service API. `AMADEUS_ENV=test` uses sandbox endpoints; `AMADEUS_ENV=production` uses live endpoints. |
| SerpAPI Google Flights | Commercial | `SERPAPI_KEY` | Optional | Easy setup and strong metasearch results, but it is a paid Google Flights API proxy rather than an open data source. |
| Kiwi / Tequila | Affiliate | `KIWI_API_KEY` | Optional | Useful for affiliate/deep links where available; setup depends on Kiwi partner/Tequila access. |

At least one provider must be configured for the bot to start. For a clean open-source setup, start with Amadeus and add optional providers only when their terms/setup fit your deployment.

### Provider Setup Difficulty Review

Tested/documented reachability as of this project revision:

- **Amadeus Self-Service** — docs and pricing pages are publicly reachable. Easiest official baseline. Sandbox works with developer credentials; production requires switching `AMADEUS_ENV=production` and enabling live access in Amadeus.
- **SerpAPI Google Flights** — docs are publicly reachable and key setup is simple. Good optional paid provider, but not an official Google Flights API.
- **Kiwi Tequila** — docs page is reachable, but product access is partner-oriented. Keep optional.
- **Official Skyscanner Partners API** — application page is reachable, but it requires partner approval. Prefer this over unofficial wrappers if accepted.
- **RapidAPI Sky-Scanner3** — removed from supported providers after a no-credential reachability check returned `HTTP 404 {"message":"API doesn't exists"}` from the host/path used by the old integration. Re-add only after verifying a maintained endpoint and terms.
- **Duffel** — docs/pricing are reachable and the API is strong for shopping + booking flows. It is not implemented yet because it is more of a booking infrastructure provider than a lightweight price-watching source.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Create or load your user profile and choose a language |
| `/newtrip` | Create a watched trip with the guided wizard |
| `/trips` | List your saved trips and open trip actions |
| `/check` | Force an immediate check for all active trips |
| `/check <trip_id>` | Force an immediate check for one trip |
| `/search JFK BCN 17/10/2026` | Run a one-way flight search |
| `/search JFK BCN 17/10/2026 01/11/2026` | Run a round-trip flight search |
| `/edit` | Edit an existing trip |
| `/settings` | Change language or currency |
| `/cancel` | Cancel the active trip or edit flow |
| `/help` | Show bot help |

## Quick Start

### Prerequisites

- Python 3.12+
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- At least one flight provider API key
- Docker, if you want to run the containerized setup

### Configure

```bash
git clone <your-repo-url>
cd FareHawk
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Configure at least one provider:
SERPAPI_KEY=
KIWI_API_KEY=
AMADEUS_API_KEY=
AMADEUS_API_SECRET=
AMADEUS_ENV=test

DATABASE_URL=sqlite:///data/farehawk.db
LOG_LEVEL=INFO
```

### Run With Docker

```bash
docker compose up -d --build
docker compose logs -f farehawk
```

For older Docker Compose installations, use `docker-compose` instead of `docker compose`.

### Run Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=$(pwd)
python bot/main.py
```

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location)
python bot/main.py
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token from BotFather |
| `SERPAPI_KEY` | One provider required | - | SerpAPI Google Flights API key |
| `KIWI_API_KEY` | One provider required | - | Kiwi Tequila API key |
| `AMADEUS_API_KEY` | With `AMADEUS_API_SECRET` | - | Amadeus Self-Service API key |
| `AMADEUS_API_SECRET` | With `AMADEUS_API_KEY` | - | Amadeus Self-Service API secret |
| `AMADEUS_ENV` | No | `test` | `test` for Amadeus sandbox endpoints, `production` for live endpoints |
| `DATABASE_URL` | No | `sqlite:///data/farehawk.db` | SQLAlchemy database URL |
| `LOG_LEVEL` | No | `INFO` | Python logging level |

## Development

Install development dependencies and run tests:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Or, with `uv`:

```bash
uv sync --dev
uv run pytest
```

The current test suite covers provider configuration, alert history evaluation, and trip ownership checks for callback actions.

## Project Structure

```text
FareHawk/
├── bot/                    # Telegram bot handlers, keyboards, and i18n
├── core/                   # Configuration, database, models, scheduler
├── providers/              # Flight provider integrations and aggregation
├── services/               # Price checks, alerts, charts, weekly digest
├── tests/                  # Pytest regression tests
├── .env.example            # Environment variable template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Data Storage And Privacy

FareHawk stores Telegram user IDs, usernames, language/currency preferences, trips, price snapshots, and alert records in the configured SQL database. The default setup uses SQLite at `data/farehawk.db` inside the container volume or local `data/` directory.

Do not commit `.env` files or database files. Treat provider keys and Telegram tokens as secrets.

## Adding A Provider

1. Create `providers/<name>.py` implementing `FlightProvider`.
2. Return normalized `FlightResult` objects from `search`.
3. Register the provider in `FlightAggregator`.
4. Add provider-specific configuration to `.env.example` and this README.
5. Add focused tests for provider activation and result parsing.

## Adding A Language

1. Create `bot/i18n/<code>.py` with a `STRINGS` dictionary.
2. Register it in `bot/i18n/__init__.py`.
3. Add a button to `language_keyboard()` in `bot/keyboards/inline.py`.

## License

MIT. See [LICENSE](LICENSE).
