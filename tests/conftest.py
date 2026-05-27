"""Test fixtures.

Integration tests require ``DATABASE_URL`` to point at a clean Postgres.
If unset, integration tests are skipped at collection time so unit tests
can still run in environments without Docker.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import metadata


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.getenv("DATABASE_URL"):
        return
    skip = pytest.mark.skip(reason="DATABASE_URL not set; skipping integration tests")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip)


@pytest_asyncio.fixture(scope="session")
async def _engine() -> AsyncIterator[object]:
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.run_sync(metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(_engine: object) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(bind=_engine, expire_on_commit=False)  # type: ignore[arg-type]
    async with factory() as s:
        yield s
        await s.rollback()
