from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config.limits import (
    COMMANDS_PER_SERVER_PER_MIN,
    COMMANDS_PER_USER_PER_MIN,
    REFRESH_INTERVAL_SECONDS_PER_WATCH,
    TRACK_INTERVAL_SECONDS_PER_USER,
)


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after: int


class BotRateLimiter:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    async def per_user_command(self, user_id: int) -> RateLimitDecision:
        return await self._window(
            f"ratelimit:cmd:user:{user_id}", limit=COMMANDS_PER_USER_PER_MIN, window=60
        )

    async def per_server_command(self, guild_id: int) -> RateLimitDecision:
        return await self._window(
            f"ratelimit:cmd:server:{guild_id}",
            limit=COMMANDS_PER_SERVER_PER_MIN,
            window=60,
        )

    async def track(self, user_id: int) -> RateLimitDecision:
        return await self._window(
            f"ratelimit:track:user:{user_id}",
            limit=1,
            window=TRACK_INTERVAL_SECONDS_PER_USER,
        )

    async def refresh(self, watch_id: str) -> RateLimitDecision:
        return await self._window(
            f"ratelimit:refresh:watch:{watch_id}",
            limit=1,
            window=REFRESH_INTERVAL_SECONDS_PER_WATCH,
        )

    async def _window(self, key: str, *, limit: int, window: int) -> RateLimitDecision:
        count = int(await self._redis.incr(key))
        if count == 1:
            await self._redis.expire(key, window)
        if count <= limit:
            return RateLimitDecision(allowed=True, retry_after=0)
        ttl = int(await self._redis.ttl(key) or window)
        return RateLimitDecision(allowed=False, retry_after=max(ttl, 1))
