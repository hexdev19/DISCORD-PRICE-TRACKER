discord-price-tracker/
├── bot/
│   ├── __init__.py
│   ├── main.py
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── tracking.py       # /track, /untrack
│   │   ├── search.py         # /search
│   │   ├── compare.py        # /compare
│   │   └── history.py        # /history listing, /history product
│   └── events/
│       ├── __init__.py
│       └── handlers.py       # on_ready, on_guild_join, on_app_command_error
├── scraper/
│   ├── __init__.py
│   ├── firecrawl_client.py
│   ├── extractor.py
│   ├── schemas.py
│   └── scrape_service.py
├── tasks/
│   ├── __init__.py
│   ├── celery_app.py
│   ├── monitor.py
│   ├── scrape_job.py
│   └── alert.py
├── services/
│   ├── __init__.py
│   ├── product_service.py
│   ├── search_service.py
│   ├── price_service.py
│   ├── history_service.py
│   └── alert_service.py
├── db/
│   ├── __init__.py
│   ├── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── store.py
│   │   ├── product.py
│   │   ├── listing.py
│   │   ├── listing_history.py
│   │   └── user_watch.py     # FK → listings · discord_user_id str
│   └── repository/
│       ├── __init__.py
│       ├── store_repo.py
│       ├── product_repo.py
│       ├── listing_repo.py
│       └── history_repo.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── embed_builder.py
│   ├── chart_builder.py
│   └── url_utils.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── logs/
│   ├── bot.log
│   ├── scraper.log
│   ├── tasks.log
│   ├── services.log
│   └── db.log
├── tests/
│   └── __init__.py
├── docker-compose.yml
├── requirements.txt
├── .env
└── alembic.ini




Rules

Every package has __init__.py. Re-export public symbols from it.
Dependency flow: cogs → services → repositories → models. Never skip or reverse.
scraper/ imports only from scraper/schemas.py. Never from services, db, or bot.
bot/ never imports from tasks/ — use .delay() only.
All helper functions go in utils/. Never define them inside services, tasks, or scrapers.
All embed construction goes in utils/embed_builder.py. Never inline in cogs.
All DB calls go in repository/. No DB in cogs or services directly.
All business logic goes in services/. No logic in repositories or cogs.
Every user-facing query scopes through user_watches.user_id — never return global listings or products.
Models use Mapped[T] + mapped_column(). All PKs are UUID. All FKs have index=True.
Repositories receive AsyncSession via constructor injection.
Log via get_logger(__name__) everywhere. Format: noun.verb with structured kwargs. Never print() or f-strings in log messages. Never log tokens, keys, or raw HTML.
Every Celery task logs on start and on completion or failure.
Type hints on every function. snake_case vars/functions · PascalCase classes · UPPER_SNAKE constants.
No inline comments unless genuinely non-obvious. No bare except. Return early over nested conditionals.
