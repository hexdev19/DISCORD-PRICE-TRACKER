from __future__ import annotations

import uuid

from app.workers.locks import ScrapeLock


class FakeRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def set(
        self, key: str, value: str, *, nx: bool = False, ex: int | None = None
    ) -> bool:
        if nx and key in self._store:
            return False
        self._store[key] = value
        return True

    async def eval(self, _script: str, _numkeys: int, key: str, value: str) -> int:
        if self._store.get(key) != value:
            return 0
        del self._store[key]
        return 1


async def test_first_acquire_succeeds_second_blocked() -> None:
    redis = FakeRedis()
    lock = ScrapeLock(redis)
    pid = uuid.uuid4()

    token = await lock.acquire(pid)
    assert token is not None

    second = await lock.acquire(pid)
    assert second is None


async def test_release_only_with_matching_token() -> None:
    redis = FakeRedis()
    lock = ScrapeLock(redis)
    pid = uuid.uuid4()
    token = await lock.acquire(pid)
    assert token is not None

    assert await lock.release(pid, "wrong-token") is False
    assert await lock.release(pid, token) is True
    assert await lock.acquire(pid) is not None


async def test_isolated_per_product() -> None:
    redis = FakeRedis()
    lock = ScrapeLock(redis)
    a = uuid.uuid4()
    b = uuid.uuid4()
    assert await lock.acquire(a) is not None
    assert await lock.acquire(b) is not None
