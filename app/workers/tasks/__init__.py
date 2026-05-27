"""Importing this package registers every Celery task with the running app."""

from __future__ import annotations

from app.workers.tasks import alert, housekeeping, maintenance, scrape  # noqa: F401
