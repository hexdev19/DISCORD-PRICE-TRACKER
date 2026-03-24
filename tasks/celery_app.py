from __future__ import annotations

from celery import Celery

from config.settings import settings


celery_app = Celery(
	"price_tracker",
	broker=settings.REDIS_URL,
	backend=settings.REDIS_URL,
	include=["tasks.scrape_job", "tasks.monitor", "tasks.alert"],
)

celery_app.conf.update(
	task_serializer="json",
	result_serializer="json",
	accept_content=["json"],
	timezone="UTC",
	enable_utc=True,
	task_routes={
		"tasks.scrape_job.*": {"queue": "scrape"},
		"tasks.monitor.*": {"queue": "monitor"},
		"tasks.alert.*": {"queue": "alerts"},
	},
)

celery_app.conf.beat_schedule = {
	"monitor-all-listings": {
		"task": "tasks.monitor.monitor_all_listings",
		"schedule": settings.MONITOR_INTERVAL,
	},
}

