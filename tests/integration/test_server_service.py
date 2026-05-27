from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.server_service import ServerService

pytestmark = pytest.mark.integration


async def test_upsert_creates_server(session: AsyncSession) -> None:
    svc = ServerService(session)
    server = await svc.upsert_from_discord(guild_id=2001, name="G1")
    await session.commit()
    assert server.is_active is True
    assert server.name == "G1"


async def test_upsert_revives_removed_server(session: AsyncSession) -> None:
    svc = ServerService(session)
    server = await svc.upsert_from_discord(guild_id=2002)
    await session.commit()

    await svc.soft_remove(2002)
    await session.commit()
    assert server.is_active is False
    assert server.removed_at is not None

    revived = await svc.upsert_from_discord(guild_id=2002, name="back")
    await session.commit()
    assert revived.id == server.id
    assert revived.is_active is True
    assert revived.removed_at is None
    assert revived.name == "back"


async def test_update_config_persists_changes(session: AsyncSession) -> None:
    svc = ServerService(session)
    server = await svc.upsert_from_discord(guild_id=2003)
    await session.commit()

    await svc.update_config(
        server.id,
        actor_id="user123",
        tracker_role_id=555,
        default_alert_channel_id=666,
        region_default="US",
    )
    await session.commit()

    assert server.tracker_role_id == 555
    assert server.default_alert_channel_id == 666
    assert server.region_default == "US"


async def test_update_config_unset_field_is_left_alone(session: AsyncSession) -> None:
    svc = ServerService(session)
    server = await svc.upsert_from_discord(guild_id=2004)
    server.tracker_role_id = 999
    await session.commit()

    await svc.update_config(server.id, actor_id="u", default_alert_channel_id=42)
    await session.commit()
    assert server.tracker_role_id == 999
    assert server.default_alert_channel_id == 42
