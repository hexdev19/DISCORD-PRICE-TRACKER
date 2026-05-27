from __future__ import annotations

import pytest

from app.config.limits import (
    CIRCUIT_FAIL_THRESHOLD,
    CIRCUIT_OPEN_INITIAL_SECONDS,
    CIRCUIT_OPEN_MAX_SECONDS,
)
from app.scraper.circuit import InMemoryCircuitBreaker


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


async def test_starts_closed(clock: FakeClock) -> None:
    cb = InMemoryCircuitBreaker(clock=clock)
    assert await cb.state("a.com") == "closed"


async def test_opens_after_threshold(clock: FakeClock) -> None:
    cb = InMemoryCircuitBreaker(clock=clock)
    for _ in range(CIRCUIT_FAIL_THRESHOLD):
        await cb.record_failure("a.com")
    assert await cb.state("a.com") == "open"


async def test_transitions_to_half_open_after_timeout(clock: FakeClock) -> None:
    cb = InMemoryCircuitBreaker(clock=clock)
    for _ in range(CIRCUIT_FAIL_THRESHOLD):
        await cb.record_failure("a.com")
    assert await cb.state("a.com") == "open"

    clock.now += CIRCUIT_OPEN_INITIAL_SECONDS + 1
    assert await cb.state("a.com") == "half_open"


async def test_success_closes_circuit(clock: FakeClock) -> None:
    cb = InMemoryCircuitBreaker(clock=clock)
    for _ in range(CIRCUIT_FAIL_THRESHOLD):
        await cb.record_failure("a.com")
    await cb.record_success("a.com")
    assert await cb.state("a.com") == "closed"


async def test_repeated_failures_double_timeout_up_to_cap(clock: FakeClock) -> None:
    cb = InMemoryCircuitBreaker(clock=clock)
    for _ in range(CIRCUIT_FAIL_THRESHOLD):
        await cb.record_failure("a.com")

    for _ in range(20):
        clock.now += CIRCUIT_OPEN_INITIAL_SECONDS * 100
        assert await cb.state("a.com") == "half_open"
        await cb.record_failure("a.com")

    assert cb._timeouts["a.com"] <= CIRCUIT_OPEN_MAX_SECONDS
