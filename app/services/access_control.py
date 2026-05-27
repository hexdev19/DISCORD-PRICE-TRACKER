from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.limits import MEMBERSHIP_CACHE_TTL_SECONDS
from app.models.membership import ServerMembership
from app.repositories.server_repo import ServerRepository
from app.services.errors import NotFound, PermissionDenied

AccessLevel = Literal["member", "admin"]


@dataclass(frozen=True, slots=True)
class MembershipSnapshot:
    is_admin: bool
    has_tracker_role: bool


class MembershipRefresher(Protocol):
    async def refresh(self, *, guild_id: int, discord_id: int) -> MembershipSnapshot | None: ...


class _NoopRefresher:
    async def refresh(self, *, guild_id: int, discord_id: int) -> MembershipSnapshot | None:
        return None


class AccessControl:
    def __init__(
        self,
        session: AsyncSession,
        *,
        refresher: MembershipRefresher | None = None,
    ) -> None:
        self.session = session
        self.servers = ServerRepository(session)
        self._refresher: MembershipRefresher = refresher or _NoopRefresher()

    async def assert_server_access(
        self,
        *,
        user_id: uuid.UUID,
        discord_id: int,
        guild_id: int,
        level: AccessLevel,
    ) -> ServerMembership:
        server = await self.servers.get_by_guild_id(guild_id)
        if server is None or not server.is_active:
            raise NotFound("server not found")

        membership = await self._get_membership(server.id, user_id)
        if membership is None or self._is_stale(membership):
            snapshot = await self._refresher.refresh(guild_id=guild_id, discord_id=discord_id)
            if snapshot is not None:
                membership = await self._upsert(server.id, user_id, snapshot)

        if membership is None:
            raise PermissionDenied("no membership recorded")

        if level == "admin" and not membership.is_admin:
            raise PermissionDenied("admin required")
        if level == "member" and not (membership.is_admin or membership.has_tracker_role):
            raise PermissionDenied("tracker role required")

        return membership

    async def _get_membership(
        self, server_id: uuid.UUID, user_id: uuid.UUID
    ) -> ServerMembership | None:
        stmt = select(ServerMembership).where(
            ServerMembership.server_id == server_id,
            ServerMembership.user_id == user_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _upsert(
        self,
        server_id: uuid.UUID,
        user_id: uuid.UUID,
        snapshot: MembershipSnapshot,
    ) -> ServerMembership:
        existing = await self._get_membership(server_id, user_id)
        now = datetime.now(timezone.utc)
        if existing is None:
            existing = ServerMembership(
                server_id=server_id,
                user_id=user_id,
                is_admin=snapshot.is_admin,
                has_tracker_role=snapshot.has_tracker_role,
                last_seen_at=now,
            )
            self.session.add(existing)
        else:
            existing.is_admin = snapshot.is_admin
            existing.has_tracker_role = snapshot.has_tracker_role
            existing.last_seen_at = now
        await self.session.flush()
        return existing

    @staticmethod
    def _is_stale(membership: ServerMembership) -> bool:
        if membership.last_seen_at is None:
            return True
        ttl = timedelta(seconds=MEMBERSHIP_CACHE_TTL_SECONDS)
        return datetime.now(timezone.utc) - membership.last_seen_at > ttl
