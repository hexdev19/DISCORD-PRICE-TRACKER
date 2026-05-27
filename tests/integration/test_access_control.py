from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.access_control import AccessControl, MembershipSnapshot
from app.services.errors import NotFound, PermissionDenied
from app.services.server_service import ServerService
from app.services.user_service import UserService

pytestmark = pytest.mark.integration


class StubRefresher:
    def __init__(self, snapshot: MembershipSnapshot | None) -> None:
        self.snapshot = snapshot
        self.calls = 0

    async def refresh(self, *, guild_id: int, discord_id: int) -> MembershipSnapshot | None:
        self.calls += 1
        return self.snapshot


async def _seed_user_and_server(
    session: AsyncSession, *, discord_id: int, guild_id: int
) -> tuple[int, int]:
    user = await UserService(session).upsert_from_discord(discord_id=discord_id)
    server = await ServerService(session).upsert_from_discord(guild_id=guild_id)
    await session.commit()
    return user.id, server.id  # type: ignore[return-value]


async def test_missing_server_raises_not_found(session: AsyncSession) -> None:
    user_id, _ = await _seed_user_and_server(session, discord_id=7001, guild_id=6001)
    ac = AccessControl(session)
    with pytest.raises(NotFound):
        await ac.assert_server_access(
            user_id=user_id, discord_id=7001, guild_id=999999, level="member"
        )


async def test_no_membership_denied(session: AsyncSession) -> None:
    user_id, _ = await _seed_user_and_server(session, discord_id=7002, guild_id=6002)
    ac = AccessControl(session)
    with pytest.raises(PermissionDenied):
        await ac.assert_server_access(
            user_id=user_id, discord_id=7002, guild_id=6002, level="member"
        )


async def test_refresher_grants_member(session: AsyncSession) -> None:
    user_id, _ = await _seed_user_and_server(session, discord_id=7003, guild_id=6003)
    refresher = StubRefresher(
        MembershipSnapshot(is_admin=False, has_tracker_role=True)
    )
    ac = AccessControl(session, refresher=refresher)
    membership = await ac.assert_server_access(
        user_id=user_id, discord_id=7003, guild_id=6003, level="member"
    )
    await session.commit()
    assert membership.has_tracker_role is True
    assert refresher.calls == 1


async def test_admin_required_denied_for_tracker_only(session: AsyncSession) -> None:
    user_id, _ = await _seed_user_and_server(session, discord_id=7004, guild_id=6004)
    refresher = StubRefresher(
        MembershipSnapshot(is_admin=False, has_tracker_role=True)
    )
    ac = AccessControl(session, refresher=refresher)
    with pytest.raises(PermissionDenied):
        await ac.assert_server_access(
            user_id=user_id, discord_id=7004, guild_id=6004, level="admin"
        )


async def test_cross_server_access_blocked(session: AsyncSession) -> None:
    """User A is a member of server A; asking about server B must fail."""
    user_id_a, _ = await _seed_user_and_server(session, discord_id=7005, guild_id=6005)
    await ServerService(session).upsert_from_discord(guild_id=6006)
    await session.commit()

    refresher = StubRefresher(None)
    ac = AccessControl(session, refresher=refresher)

    with pytest.raises(PermissionDenied):
        await ac.assert_server_access(
            user_id=user_id_a, discord_id=7005, guild_id=6006, level="member"
        )
