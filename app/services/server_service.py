from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.server import Server
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.server_repo import ServerRepository
from app.services.errors import NotFound


class _Unset:
    pass


_UNSET = _Unset()


class ServerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.servers = ServerRepository(session)
        self.audit = AuditLogRepository(session)

    async def upsert_from_discord(
        self,
        *,
        guild_id: int,
        name: str | None = None,
        icon_hash: str | None = None,
    ) -> Server:
        server = await self.servers.get_by_guild_id(guild_id)
        if server is None:
            server = await self.servers.create(guild_id=guild_id, name=name)
            if icon_hash is not None:
                server.icon_hash = icon_hash
            await self.audit.record(
                action="server.joined",
                actor_type="system",
                server_id=server.id,
                target_type="server",
                target_id=str(server.id),
            )
            return server
        revived = False
        if not server.is_active:
            server.is_active = True
            server.removed_at = None
            revived = True
        if name is not None:
            server.name = name
        if icon_hash is not None:
            server.icon_hash = icon_hash
        await self.session.flush()
        if revived:
            await self.audit.record(
                action="server.rejoined",
                actor_type="system",
                server_id=server.id,
                target_type="server",
                target_id=str(server.id),
            )
        return server

    async def update_config(
        self,
        server_id: uuid.UUID,
        *,
        actor_id: str,
        tracker_role_id: int | None | _Unset = _UNSET,
        default_alert_channel_id: int | None | _Unset = _UNSET,
        default_alert_role_id: int | None | _Unset = _UNSET,
        region_default: str | None | _Unset = _UNSET,
    ) -> Server:
        server = await self._require_active(server_id)
        changes: dict[str, Any] = {}
        if not isinstance(tracker_role_id, _Unset):
            server.tracker_role_id = tracker_role_id
            changes["tracker_role_id"] = tracker_role_id
        if not isinstance(default_alert_channel_id, _Unset):
            server.default_alert_channel_id = default_alert_channel_id
            changes["default_alert_channel_id"] = default_alert_channel_id
        if not isinstance(default_alert_role_id, _Unset):
            server.default_alert_role_id = default_alert_role_id
            changes["default_alert_role_id"] = default_alert_role_id
        if not isinstance(region_default, _Unset):
            server.region_default = region_default
            changes["region_default"] = region_default
        if changes:
            await self.audit.record(
                action="server.config.updated",
                actor_type="user",
                actor_id=actor_id,
                server_id=server.id,
                target_type="server",
                target_id=str(server.id),
                payload=changes,
            )
        return server

    async def soft_remove(self, guild_id: int) -> Server | None:
        server = await self.servers.get_by_guild_id(guild_id)
        if server is None or not server.is_active:
            return server
        server.is_active = False
        server.removed_at = datetime.now(timezone.utc)
        await self.audit.record(
            action="server.removed",
            actor_type="system",
            server_id=server.id,
            target_type="server",
            target_id=str(server.id),
        )
        return server

    async def _require_active(self, server_id: uuid.UUID) -> Server:
        server = await self.servers.get(server_id)
        if server is None or not server.is_active:
            raise NotFound("server not found")
        return server
