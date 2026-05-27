from __future__ import annotations

import uuid
from typing import Any, Literal, Protocol

Priority = Literal["normal", "high"]


class TaskQueue(Protocol):
    def send_task(self, name: str, *, args: list[Any], queue: str) -> None: ...


class CeleryTaskQueue:
    def __init__(self, celery_app: Any) -> None:
        self._app = celery_app

    def send_task(self, name: str, *, args: list[Any], queue: str) -> None:
        self._app.send_task(name, args=args, queue=queue)


_queue: TaskQueue | None = None


def configure(queue: TaskQueue) -> None:
    global _queue
    _queue = queue


def _require_queue() -> TaskQueue:
    if _queue is None:
        raise RuntimeError("task queue not configured; call services.queue.configure() at boot")
    return _queue


def enqueue_scrape(product_id: uuid.UUID, *, priority: Priority = "normal") -> None:
    target = "scrape.adapter" if priority == "high" else "scrape.normal"
    _require_queue().send_task("scrape.product", args=[str(product_id)], queue=target)


def enqueue_alert_dispatch(alert_event_id: int) -> None:
    _require_queue().send_task("alert.dispatch", args=[alert_event_id], queue="alert")
