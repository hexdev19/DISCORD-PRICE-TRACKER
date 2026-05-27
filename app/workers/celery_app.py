from __future__ import annotations

from celery import Celery
from celery.signals import worker_process_init

from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.sentry import init_sentry
from app.observability.tracing import init_tracing
from app.services import queue
from app.workers.schedule import BEAT_SCHEDULE

settings = get_settings()

celery_app = Celery(
    "price_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_queue="scrape.normal",
    task_routes={
        "scrape.tick": {"queue": "maintenance"},
        "scrape.product": {"queue": "scrape.normal"},
        "alert.evaluate": {"queue": "alert"},
        "alert.dispatch": {"queue": "alert"},
        "maintenance.refresh_fx": {"queue": "maintenance"},
        "maintenance.prune_snapshots": {"queue": "maintenance"},
        "maintenance.circuit_probe": {"queue": "maintenance"},
        "maintenance.cleanup_servers": {"queue": "maintenance"},
        "maintenance.cleanup_accounts": {"queue": "maintenance"},
    },
    beat_schedule=BEAT_SCHEDULE,
)

queue.configure(queue.CeleryTaskQueue(celery_app))


@worker_process_init.connect
def _init_worker(**_kwargs: object) -> None:
    configure_logging(settings.log_level)
    init_sentry("workers")
    init_tracing("workers")


from app.workers.tasks import alert, housekeeping, maintenance, scrape  # noqa: E402,F401
