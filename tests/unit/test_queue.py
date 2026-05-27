from __future__ import annotations

import uuid

import pytest

from app.services import queue


class RecordingQueue:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list, str]] = []

    def send_task(self, name: str, *, args: list, queue: str) -> None:
        self.calls.append((name, args, queue))


@pytest.fixture(autouse=True)
def _reset_queue() -> None:
    queue.configure(RecordingQueue())


def test_enqueue_scrape_normal_priority() -> None:
    fake = RecordingQueue()
    queue.configure(fake)
    pid = uuid.uuid4()
    queue.enqueue_scrape(pid)
    assert fake.calls == [("scrape.product", [str(pid)], "scrape.normal")]


def test_enqueue_scrape_high_priority_routes_to_adapter_queue() -> None:
    fake = RecordingQueue()
    queue.configure(fake)
    pid = uuid.uuid4()
    queue.enqueue_scrape(pid, priority="high")
    assert fake.calls == [("scrape.product", [str(pid)], "scrape.adapter")]


def test_enqueue_alert_dispatch_routes_to_alert_queue() -> None:
    fake = RecordingQueue()
    queue.configure(fake)
    queue.enqueue_alert_dispatch(42)
    assert fake.calls == [("alert.dispatch", [42], "alert")]


def test_requires_configuration() -> None:
    queue._queue = None  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        queue.enqueue_scrape(uuid.uuid4())
