# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Discord-first price tracker bot with a Next.js read-only dashboard. Modular monolith in one Python codebase, deployed as **three Python processes** — `api` (FastAPI), `bot` (discord.py), `workers` (Celery + beat) — sharing Postgres + Redis. Python 3.12.

`planning/` (gitignored) holds the source-of-truth architecture, PRD, ADRs, data model, and per-phase implementation plan. Read those when in doubt — `architecture.md`, `decisions.md`, and `implementation-plan.md` are the most load-bearing.

## Commands

```powershell
# Install (all extras needed for full local dev)
pip install -e ".[dev,api,bot,workers]"

# Local infra (Postgres on :5433, Redis on :6380 — note non-default ports)
docker compose -f docker-compose.dev.yml up -d

# Lint / format / type-check
ruff check .
ruff format --check .
mypy app                    # runs in --strict mode (configured in pyproject)

# Migrations (DSN resolved from settings, not alembic.ini)
alembic upgrade head
alembic downgrade base
alembic revision --autogenerate -m "msg"

# Tests
pytest                                          # unit only if DATABASE_URL unset
pytest tests/unit/test_router.py                # single file
pytest tests/unit/test_router.py::test_name     # single test
pytest -m integration                           # requires DATABASE_URL
pytest --cov=app --cov-report=term-missing

# Run a process locally (each is a separate entrypoint)
python -m app.bot.main
celery -A app.workers.celery_app worker -Q scrape.normal,scrape.adapter,alert,maintenance -l info
celery -A app.workers.celery_app beat -l info
uvicorn app.api.main:app --reload
```

Integration tests auto-skip at collection time when `DATABASE_URL` is unset (see `tests/conftest.py`). CI sets it and runs the full suite plus a migration round-trip.

## Architecture rules (enforced — don't violate)

Dependency direction is strict and CI-checked:

```
cogs / routers / tasks  →  services  →  repositories  →  models
```

1. **`scraper/`** imports only `scraper/schemas`, `scraper/normalize`, and `utils/`. Never from `services`, `repositories`, `models`, `bot`, `api`.
2. **`bot/` and `api/` never import `app.workers.*`.** They enqueue through `app/services/queue.py` (a thin `celery.send_task` wrapper). There's a unit test (`tests/unit/test_no_worker_imports.py`) that asserts this.
3. **All DB access lives in `repositories/`.** No SQLAlchemy queries in services, cogs, routers, or tasks.
4. **All business logic lives in `services/`.** Repos are CRUD only; cogs, routers, tasks are thin.
5. **Embed construction goes through `utils/embed_builder`.** No inline embed dicts in cogs.
6. **User-scoped reads pass through `services/access_control.py`.** Never resolve a watch / server by raw ID without authorizing.
7. **All numeric caps live in `app/config/limits.py`** (watches per server, cadence, rate limits, retention, etc.). Never hardcode.
8. **No `print()` anywhere in `app/`** — ruff rule `T20` enforces this. Use `get_logger(__name__)` from `app.utils.logger` with structured kwargs. CI also greps for `logger.*\(.*token` to prevent token leaks in logs.
9. **Type hints on every public function.** mypy `--strict` is mandatory.

## Scraper: four-tier router

`app/scraper/router.py` cascades from cheapest to most expensive:

1. **Structured data** (JSON-LD / microdata / OG) — `structured.py`
2. **Scrapling auto-extract** — `autoextract.py`
3. **Per-site HTTP adapter** — `adapters/{amazon,ebay,aliexpress,walmart,bestbuy,target}.py`
4. **Stealthy browser** (Scrapling `StealthyFetcher`, Patchright-based) — `browser.py`, capped at `max_pages=2`

Each domain has a circuit breaker (`circuit.py`); when open, scrapes short-circuit at tier 0. Adapters declare `needs_browser` — adapter-only sites skip Tier 1/2 fetch entirely.

When adding an adapter, ship a fixture under `tests/fixtures/adapters/<name>/example.html` and a `tests/unit/test_adapters.py` case — the exit criterion for the scraper phase is "every adapter extracts its fixture into a valid `ScrapeResult`."

## Queue seam

`app/services/queue.py` is the *only* boundary between bot/API and workers. It exposes `enqueue_scrape(product_id, priority=...)` and `enqueue_alert_dispatch(alert_event_id)`. Bot and API call `queue.configure(CeleryTaskQueue(celery_client))` at boot; worker process registers itself in `app/workers/celery_app.py`. Adding a new task type means: define it in `workers/tasks/`, route it in `celery_app.py`'s `task_routes`, and expose a typed enqueue helper in `services/queue.py`.

Celery queues: `scrape.normal`, `scrape.adapter` (high priority), `alert`, `maintenance`. Beat schedule lives in `app/workers/schedule.py`.

## Data model conventions

- **Prices stored in native currency** — never USD-normalized at scrape time (ADR-006). Display layer does the FX conversion via the daily `fx_rate` snapshot.
- **One `products` row per canonicalized URL** — shared across servers tracking the same URL (ADR-008). URL canonicalization lives in `utils/url_utils.py` (which also contains the SSRF guard).
- **Server-only at MVP** — no DM watches (ADR-002). Bot redirects DMs.
- Models: `user`, `server`, `product`, `watch`, `price_snapshot`, `alert_event`, `membership`, `fx_rate`, `audit_log`. All under `app/models/`.

## Config

`app/config/settings.py` (pydantic-settings) reads `.env.local` in dev — fails loud on missing required vars. `app/config/limits.py` is the single source of truth for every numeric cap; envs override individual values. See `.env.example` for the full var list.

## Observability

Wired from day one (ADR-012): structlog JSON to stdout, Sentry per process, OpenTelemetry with auto-instrumentation for FastAPI / SQLAlchemy / Celery, Prometheus on `/metrics`. Each entrypoint calls `configure_logging` → `init_sentry(service)` → `init_tracing(service)` before doing anything else.
