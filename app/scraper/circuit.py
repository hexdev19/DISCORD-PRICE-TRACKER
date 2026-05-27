"""Per-domain circuit breaker.

State and timeouts live in Redis so workers share a single view; an
in-memory implementation is provided for tests. Defaults come from
``app.config.limits`` (ADR-011).
"""

from __future__ import annotations

import time
from typing import Literal, Protocol

from app.config.limits import (
    CIRCUIT_FAIL_THRESHOLD,
    CIRCUIT_OPEN_INITIAL_SECONDS,
    CIRCUIT_OPEN_MAX_SECONDS,
)

CircuitState = Literal["closed", "open", "half_open"]


class CircuitBreaker(Protocol):
    async def state(self, domain: str) -> CircuitState: ...
    async def record_success(self, domain: str) -> None: ...
    async def record_failure(self, domain: str) -> None: ...


class InMemoryCircuitBreaker:
    def __init__(self, *, clock: "Clock | None" = None) -> None:
        self._clock = clock or _real_clock
        self._fail_counts: dict[str, int] = {}
        self._opened_at: dict[str, float] = {}
        self._timeouts: dict[str, float] = {}

    async def state(self, domain: str) -> CircuitState:
        opened = self._opened_at.get(domain)
        if opened is None:
            return "closed"
        timeout = self._timeouts.get(domain, CIRCUIT_OPEN_INITIAL_SECONDS)
        if self._clock() - opened >= timeout:
            return "half_open"
        return "open"

    async def record_success(self, domain: str) -> None:
        self._fail_counts.pop(domain, None)
        self._opened_at.pop(domain, None)
        self._timeouts.pop(domain, None)

    async def record_failure(self, domain: str) -> None:
        if self._opened_at.get(domain) is not None:
            current = self._timeouts.get(domain, CIRCUIT_OPEN_INITIAL_SECONDS)
            self._timeouts[domain] = min(current * 2, CIRCUIT_OPEN_MAX_SECONDS)
            self._opened_at[domain] = self._clock()
            return
        count = self._fail_counts.get(domain, 0) + 1
        self._fail_counts[domain] = count
        if count >= CIRCUIT_FAIL_THRESHOLD:
            self._opened_at[domain] = self._clock()
            self._timeouts[domain] = CIRCUIT_OPEN_INITIAL_SECONDS


class Clock(Protocol):
    def __call__(self) -> float: ...


def _real_clock() -> float:
    return time.monotonic()


class RedisCircuitBreaker:
    """Redis-backed shared circuit breaker.

    Keys:
        circuit:{domain}:state        -> "closed"|"open"|"half_open"
        circuit:{domain}:fails        -> int (closed-state counter)
        circuit:{domain}:opened_at    -> float monotonic
        circuit:{domain}:timeout      -> float seconds
    """

    def __init__(self, redis: object) -> None:
        self._redis = redis

    async def state(self, domain: str) -> CircuitState:
        opened_raw = await self._get(f"circuit:{domain}:opened_at")
        if opened_raw is None:
            return "closed"
        timeout = float(await self._get(f"circuit:{domain}:timeout") or CIRCUIT_OPEN_INITIAL_SECONDS)
        if time.time() - float(opened_raw) >= timeout:
            return "half_open"
        return "open"

    async def record_success(self, domain: str) -> None:
        await self._del(
            f"circuit:{domain}:fails",
            f"circuit:{domain}:opened_at",
            f"circuit:{domain}:timeout",
        )

    async def record_failure(self, domain: str) -> None:
        opened_raw = await self._get(f"circuit:{domain}:opened_at")
        if opened_raw is not None:
            current = float(
                await self._get(f"circuit:{domain}:timeout") or CIRCUIT_OPEN_INITIAL_SECONDS
            )
            new_timeout = min(current * 2, CIRCUIT_OPEN_MAX_SECONDS)
            await self._set(f"circuit:{domain}:timeout", new_timeout)
            await self._set(f"circuit:{domain}:opened_at", time.time())
            return
        count = await self._incr(f"circuit:{domain}:fails")
        if count >= CIRCUIT_FAIL_THRESHOLD:
            await self._set(f"circuit:{domain}:opened_at", time.time())
            await self._set(f"circuit:{domain}:timeout", float(CIRCUIT_OPEN_INITIAL_SECONDS))

    async def _get(self, key: str) -> bytes | str | None:
        return await self._redis.get(key)  # type: ignore[attr-defined]

    async def _set(self, key: str, value: float | int | str) -> None:
        await self._redis.set(key, value)  # type: ignore[attr-defined]

    async def _del(self, *keys: str) -> None:
        if keys:
            await self._redis.delete(*keys)  # type: ignore[attr-defined]

    async def _incr(self, key: str) -> int:
        return int(await self._redis.incr(key))  # type: ignore[attr-defined]
