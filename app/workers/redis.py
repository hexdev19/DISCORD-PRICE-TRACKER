from __future__ import annotations

from typing import Any

import redis
import redis.asyncio as aredis

from app.config.settings import get_settings

_async_client: aredis.Redis | None = None
_sync_client: redis.Redis | None = None


def async_client() -> aredis.Redis:
    global _async_client
    if _async_client is None:
        _async_client = aredis.from_url(
            get_settings().redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _async_client


def sync_client() -> redis.Redis:
    global _sync_client
    if _sync_client is None:
        _sync_client = redis.from_url(
            get_settings().redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _sync_client


async def close_async() -> None:
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None


def _reset_for_tests(*, async_: Any = None, sync_: Any = None) -> None:
    global _async_client, _sync_client
    _async_client = async_
    _sync_client = sync_
