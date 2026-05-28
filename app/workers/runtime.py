from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import redis.asyncio as aredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config.settings import get_settings


@dataclass(slots=True)
class WorkerRuntime:
    session_factory: async_sessionmaker[AsyncSession]
    redis: aredis.Redis


@asynccontextmanager
async def worker_runtime() -> AsyncIterator[WorkerRuntime]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, poolclass=NullPool, future=True)
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, autoflush=False
    )
    redis_client: aredis.Redis = aredis.from_url(  # type: ignore[no-untyped-call]
        settings.redis_url, encoding="utf-8", decode_responses=True
    )
    try:
        yield WorkerRuntime(session_factory=session_factory, redis=redis_client)
    finally:
        await redis_client.aclose()
        await engine.dispose()
