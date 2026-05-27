"""Per-domain politeness limiter.

Fixed 60-second window: at most ``DOMAIN_REQUESTS_PER_MIN`` requests per
domain. INCR + EXPIRE is atomic enough for this use case (no need for a
full token bucket at MVP).
"""

from __future__ import annotations

from typing import Any

from app.config.limits import DOMAIN_REQUESTS_PER_MIN


class DomainRateLimiter:
    def __init__(self, redis: Any, *, capacity: int = DOMAIN_REQUESTS_PER_MIN) -> None:
        self._redis = redis
        self._capacity = capacity

    async def try_acquire(self, domain: str) -> bool:
        key = f"ratelimit:domain:{domain}"
        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, 60)
        return count <= self._capacity
