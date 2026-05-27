"""Per-product scrape lock.

``acquire`` uses ``SETNX + EX`` so a single product can never be scraped
concurrently by two workers; ``release`` matches the value to avoid
deleting a lock another worker has rotated in.
"""

from __future__ import annotations

import secrets
import uuid
from typing import Any

from app.config.limits import SCRAPE_LOCK_TTL_SECONDS

_RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
"""


class ScrapeLock:
    def __init__(self, redis: Any) -> None:
        self._redis = redis

    @staticmethod
    def _key(product_id: uuid.UUID) -> str:
        return f"scrape:product:{product_id}"

    async def acquire(self, product_id: uuid.UUID) -> str | None:
        token = secrets.token_hex(16)
        ok = await self._redis.set(
            self._key(product_id), token, nx=True, ex=SCRAPE_LOCK_TTL_SECONDS
        )
        return token if ok else None

    async def release(self, product_id: uuid.UUID, token: str) -> bool:
        result = await self._redis.eval(_RELEASE_LUA, 1, self._key(product_id), token)
        return int(result) == 1
