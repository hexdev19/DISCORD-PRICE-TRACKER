from __future__ import annotations

import pytest

from app.workers.rate_limit import DomainRateLimiter


class FakeRedis:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}
        self.expires: list[tuple[str, int]] = []

    async def incr(self, key: str) -> int:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expires.append((key, seconds))


async def test_first_request_passes_and_sets_window() -> None:
    redis = FakeRedis()
    limiter = DomainRateLimiter(redis, capacity=3)
    assert await limiter.try_acquire("example.com") is True
    assert redis.expires == [("ratelimit:domain:example.com", 60)]


async def test_subsequent_requests_within_capacity_pass() -> None:
    redis = FakeRedis()
    limiter = DomainRateLimiter(redis, capacity=3)
    assert [await limiter.try_acquire("e.com") for _ in range(3)] == [True, True, True]


async def test_overage_rejected() -> None:
    redis = FakeRedis()
    limiter = DomainRateLimiter(redis, capacity=2)
    assert await limiter.try_acquire("e.com") is True
    assert await limiter.try_acquire("e.com") is True
    assert await limiter.try_acquire("e.com") is False


@pytest.mark.asyncio
async def test_isolated_per_domain() -> None:
    redis = FakeRedis()
    limiter = DomainRateLimiter(redis, capacity=1)
    assert await limiter.try_acquire("a.com") is True
    assert await limiter.try_acquire("b.com") is True
    assert await limiter.try_acquire("a.com") is False
