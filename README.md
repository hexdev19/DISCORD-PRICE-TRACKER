# Discord Price Tracker

Discord-first price tracker bot with a Next.js read-only dashboard. Users manage product price watches through Discord slash commands; price history, charts, and watch management are available via the web dashboard.

Modular monolith deployed as three Python processes (FastAPI API, discord.py bot, Celery workers + beat) plus a Next.js frontend, sharing Postgres and Redis.

## Key Features

- **Discord-native watch management** — slash commands to add, list, remove, and refresh price watches per server
- **Multi-tier scraper** — cascades from structured data (JSON-LD/microdata) through auto-extract and per-site HTTP adapters to stealthy browser, with domain-level circuit breakers
- **Adapter-based retailer support** — dedicated extractors for Amazon, eBay, AliExpress, Walmart, BestBuy, Target
- **Price drop alerts** — confidence-scored evaluation with configurable cooldown (drop, restock thresholds)
- **Price history** — configurable retention, stored in native currency with daily FX snapshots
- **Read-only dashboard** — Next.js 15 App Router showing servers, watches, and price charts via FastAPI REST
- **Full observability** — structlog JSON logging, Sentry error tracking, OpenTelemetry tracing, Prometheus metrics

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12 |
| API | FastAPI / Uvicorn |
| Bot | discord.py 2.x |
| Workers | Celery 5.x + Redis (broker/backend) |
| ORM | SQLAlchemy 2.x (async) + asyncpg |
| Migrations | Alembic |
| Scraping | Scrapling (auto-extract, stealthy browser via Patchright/Chromium), per-site HTTP adapters, Firecrawl fallback |
| Dashboard | Next.js 15, React 19, TypeScript, Tailwind CSS 4 |
| Observability | structlog, Sentry, OpenTelemetry (OTLP gRPC), Prometheus |

## Project Structure

```
├── app/
│   ├── api/              # FastAPI REST (routers, auth, deps, error handlers)
│   ├── bot/              # discord.py gateway (cogs, events, permissions)
│   ├── config/           # pydantic-settings + numeric limits
│   ├── db/               # async session factory, Alembic migrations
│   ├── models/           # SQLAlchemy ORM (User, Server, Product, Watch, etc.)
│   ├── observability/    # Logging, Sentry, OpenTelemetry init
│   ├── repositories/     # CRUD DAOs (no business logic)
│   ├── scraper/          # Tiered scraper (structured → auto → adapters → browser)
│   ├── services/         # Business logic, task queue seam, alert evaluation
│   ├── utils/            # Embed builder, URL utils (canonicalization, SSRF guard), logging helpers
│   └── workers/          # Celery app, beat schedule, task definitions
├── dashboard/            # Next.js 15 App Router (read-only)
├── docker/               # Dockerfiles per service (api, bot, worker, beat, dashboard)
├── tests/                # Pytest (unit, integration, e2e, fixtures)
├── planning/             # Architecture docs, PRD, ADRs, implementation plans
├── docker-compose.yml    # Production deployment
├── docker-compose.dev.yml # Local infra (Postgres :5433, Redis :6380)
└── pyproject.toml        # Dependencies, ruff, mypy, pytest config
```

## Local Development

```powershell
# Install with all extras
pip install -e ".[dev,api,bot,workers]"

# Start local Postgres and Redis (non-default ports)
docker compose -f docker-compose.dev.yml up -d

# Run database migrations
alembic upgrade head

# Lint / format / type-check
ruff check .
ruff format --check .
mypy app
```

### Running individual processes

```powershell
# Discord bot (gateway + slash commands)
python -m app.bot.main

# FastAPI REST API
uvicorn app.api.main:app --reload

# Celery worker (subscribe to specific queues)
celery -A app.workers.celery_app worker -Q scrape.normal,scrape.adapter,alert,maintenance -l info

# Celery beat scheduler
celery -A app.workers.celery_app beat -l info
```

### Tests

```powershell
pytest                         # unit only (no DB required)
pytest -m integration          # requires DATABASE_URL
pytest --cov=app --cov-report=term-missing
```

## Docker (Production)

```bash
docker compose up -d

## Required Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres DSN (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis DSN (`redis://...`) |
| `DISCORD_TOKEN` | Discord bot token |
| `DISCORD_CLIENT_ID` | Discord OAuth2 client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 client secret |
| `SESSION_COOKIE_SECRET` | Session encryption key (min 32 chars) |
| `OAUTH_TOKEN_ENC_KEY` | OAuth token encryption key (min 32 chars) |
