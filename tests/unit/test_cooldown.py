from __future__ import annotations

from app.services.cooldown import InMemoryCooldownStore


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_set_then_expire() -> None:
    clock = FakeClock()
    store = InMemoryCooldownStore(clock=clock)
    await store.set_cooldown("k", 60)
    assert await store.is_cooling("k") is True
    clock.now += 30
    assert await store.is_cooling("k") is True
    clock.now += 31
    assert await store.is_cooling("k") is False


async def test_missing_key_not_cooling() -> None:
    store = InMemoryCooldownStore()
    assert await store.is_cooling("nope") is False
