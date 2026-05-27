from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.errors import NotFound
from app.services.user_service import UserService

pytestmark = pytest.mark.integration


async def test_upsert_creates_then_updates(session: AsyncSession) -> None:
    svc = UserService(session)

    created = await svc.upsert_from_discord(discord_id=1001, discord_username="alice")
    await session.commit()
    assert created.discord_username == "alice"

    updated = await svc.upsert_from_discord(discord_id=1001, discord_username="alice2")
    await session.commit()
    assert updated.id == created.id
    assert updated.discord_username == "alice2"


async def test_soft_delete_sets_deleted_at(session: AsyncSession) -> None:
    svc = UserService(session)
    user = await svc.upsert_from_discord(discord_id=1002)
    await session.commit()

    await svc.soft_delete(user.id)
    await session.commit()
    assert user.deleted_at is not None


async def test_soft_delete_missing_raises(session: AsyncSession) -> None:
    import uuid

    svc = UserService(session)
    with pytest.raises(NotFound):
        await svc.soft_delete(uuid.uuid4())
