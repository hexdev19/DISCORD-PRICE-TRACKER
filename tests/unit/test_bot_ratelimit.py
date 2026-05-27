from __future__ import annotations

from app.bot.ratelimit import BotRateLimiter
from app.config.limits import COMMANDS_PER_USER_PER_MIN


class FakeRedis:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.ttls[key] = seconds

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, 60)


async def test_per_user_first_call_allowed_sets_window() -> None:
    redis = FakeRedis()
    limiter = BotRateLimiter(redis)
    decision = await limiter.per_user_command(user_id=1)
    assert decision.allowed is True
    assert redis.ttls["ratelimit:cmd:user:1"] == 60


async def test_per_user_blocks_after_limit() -> None:
    redis = FakeRedis()
    limiter = BotRateLimiter(redis)
    for _ in range(COMMANDS_PER_USER_PER_MIN):
        decision = await limiter.per_user_command(user_id=2)
        assert decision.allowed is True
    blocked = await limiter.per_user_command(user_id=2)
    assert blocked.allowed is False
    assert blocked.retry_after >= 1


async def test_track_window_is_seconds_not_minutes() -> None:
    redis = FakeRedis()
    limiter = BotRateLimiter(redis)
    await limiter.track(user_id=3)
    blocked = await limiter.track(user_id=3)
    assert blocked.allowed is False
