from __future__ import annotations

from typing import Any

from celery.schedules import crontab

BEAT_SCHEDULE: dict[str, dict[str, Any]] = {
    "scrape-tick": {
        "task": "scrape.tick",
        "schedule": crontab(minute="*/5"),
    },
    "circuit-probe": {
        "task": "maintenance.circuit_probe",
        "schedule": crontab(minute=0),
    },
    "refresh-fx": {
        "task": "maintenance.refresh_fx",
        "schedule": crontab(hour=3, minute=0),
    },
    "prune-snapshots": {
        "task": "maintenance.prune_snapshots",
        "schedule": crontab(hour=4, minute=0),
    },
    "cleanup-servers": {
        "task": "maintenance.cleanup_servers",
        "schedule": crontab(hour=5, minute=0, day_of_week="sun"),
    },
    "cleanup-accounts": {
        "task": "maintenance.cleanup_accounts",
        "schedule": crontab(hour=5, minute=30, day_of_week="sun"),
    },
}
