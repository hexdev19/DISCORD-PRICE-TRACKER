from __future__ import annotations

import time
from typing import Any, Protocol


class CooldownStore(Protocol):
    async def is_cooling(self, key: str) -> bool: ...
    async def set_cooldown(self, key: str, ttl_seconds: int) -> None: ...


class InMemoryCooldownStore:
    def __init__(self, *, clock: Any = None) -> None:
        self._clock = clock or time.time
        self._expiry: dict[str, float] = {}

    async def is_cooling(self, key: str) -> bool:
        expiry = self._expiry.get(key)
        return expiry is not None and expiry > self._clock()

    async def set_cooldown(self, key: str, ttl_seconds: int) -> None:
        self._expiry[key] = self._clock() + ttl_seconds


class RedisCooldownStore:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    async def is_cooling(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def set_cooldown(self, key: str, ttl_seconds: int) -> None:
        await self._redis.set(key, "1", ex=ttl_seconds)
