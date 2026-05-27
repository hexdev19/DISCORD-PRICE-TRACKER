from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.limits import WATCHES_PER_SERVER, WATCHES_PER_USER_PER_SERVER
from app.models.server import Server
from app.models.user import User
from app.models.watch import Watch
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.server_repo import ServerRepository
from app.repositories.user_repo import UserRepository
from app.repositories.watch_repo import WatchRepository
from app.services import queue
from app.services.errors import (
    AlreadyExists,
    LimitExceeded,
    NotFound,
    PermissionDenied,
)
from app.services.product_service import ProductService

DEFAULT_ALERT_RULES: dict[str, Any] = {"drop": True, "restock": True}


class WatchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.watches = WatchRepository(session)
        self.servers = ServerRepository(session)
        self.users = UserRepository(session)
        self.audit = AuditLogRepository(session)
        self.products = ProductService(session)

    async def add_watch(
        self,
        *,
        guild_id: int,
        discord_user_id: int,
        raw_url: str,
    ) -> Watch:
        server, user = await self._resolve_actors(guild_id, discord_user_id)

        server_count = await self.watches.count_active_for_server(server.id)
        server_cap = WATCHES_PER_SERVER[server.plan]
        if server_count >= server_cap:
            raise LimitExceeded(limit_name="watches_per_server", value=server_cap)

        user_count = await self.watches.count_for_user_in_server(server.id, user.id)
        user_cap = WATCHES_PER_USER_PER_SERVER[server.plan]
        if user_count >= user_cap:
            raise LimitExceeded(limit_name="watches_per_user_per_server", value=user_cap)

        product, _created = await self.products.find_or_create_by_url(
            raw_url, region=server.region_default
        )

        existing = await self.watches.get_by_server_and_product(server.id, product.id)
        if existing is not None:
            raise AlreadyExists(f"already tracked as {existing.short_id}")

        watch = await self.watches.create(
            server_id=server.id,
            added_by_user_id=user.id,
            product_id=product.id,
            alert_rules=dict(DEFAULT_ALERT_RULES),
        )
        await self.audit.record(
            action="watch.created",
            actor_type="user",
            actor_id=str(discord_user_id),
            server_id=server.id,
            target_type="watch",
            target_id=str(watch.id),
            payload={"product_id": str(product.id), "short_id": watch.short_id},
        )
        return watch

    async def update_alert_rules(
        self,
        *,
        watch_id: uuid.UUID,
        discord_user_id: int,
        is_admin: bool,
        rules: dict[str, Any],
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        await self._require_owner_or_admin(watch, discord_user_id, is_admin)
        watch.alert_rules = {**watch.alert_rules, **rules}
        await self.audit.record(
            action="watch.rules.updated",
            actor_type="user",
            actor_id=str(discord_user_id),
            server_id=watch.server_id,
            target_type="watch",
            target_id=str(watch.id),
            payload=rules,
        )
        return watch

    async def set_channel(
        self,
        *,
        watch_id: uuid.UUID,
        discord_user_id: int,
        channel_id: int | None,
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        watch.alert_channel_id = channel_id
        await self.audit.record(
            action="watch.channel.updated",
            actor_type="user",
            actor_id=str(discord_user_id),
            server_id=watch.server_id,
            target_type="watch",
            target_id=str(watch.id),
            payload={"channel_id": channel_id},
        )
        return watch

    async def set_role_mention(
        self,
        *,
        watch_id: uuid.UUID,
        discord_user_id: int,
        role_id: int | None,
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        watch.alert_role_id = role_id
        await self.audit.record(
            action="watch.role.updated",
            actor_type="user",
            actor_id=str(discord_user_id),
            server_id=watch.server_id,
            target_type="watch",
            target_id=str(watch.id),
            payload={"role_id": role_id},
        )
        return watch

    async def pause(
        self, *, watch_id: uuid.UUID, discord_user_id: int, is_admin: bool
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        await self._require_owner_or_admin(watch, discord_user_id, is_admin)
        watch.paused_at = datetime.now(timezone.utc)
        return watch

    async def resume(
        self, *, watch_id: uuid.UUID, discord_user_id: int, is_admin: bool
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        await self._require_owner_or_admin(watch, discord_user_id, is_admin)
        watch.paused_at = None
        return watch

    async def remove(
        self, *, watch_id: uuid.UUID, discord_user_id: int, is_admin: bool
    ) -> None:
        watch = await self._require_watch(watch_id)
        await self._require_owner_or_admin(watch, discord_user_id, is_admin)
        watch.removed_at = datetime.now(timezone.utc)
        await self.audit.record(
            action="watch.deleted",
            actor_type="user",
            actor_id=str(discord_user_id),
            server_id=watch.server_id,
            target_type="watch",
            target_id=str(watch.id),
        )

    async def request_refresh(
        self, *, watch_id: uuid.UUID, discord_user_id: int, is_admin: bool
    ) -> Watch:
        watch = await self._require_watch(watch_id)
        await self._require_owner_or_admin(watch, discord_user_id, is_admin)
        queue.enqueue_scrape(watch.product_id, priority="high")
        return watch

    async def _resolve_actors(
        self, guild_id: int, discord_user_id: int
    ) -> tuple[Server, User]:
        server = await self.servers.get_by_guild_id(guild_id)
        if server is None or not server.is_active:
            raise NotFound("server not registered")
        user = await self.users.get_by_discord_id(discord_user_id)
        if user is None:
            raise NotFound("user not registered")
        return server, user

    async def _require_watch(self, watch_id: uuid.UUID) -> Watch:
        watch = await self.watches.get(watch_id)
        if watch is None or watch.removed_at is not None:
            raise NotFound("watch not found")
        return watch

    async def _require_owner_or_admin(
        self, watch: Watch, discord_user_id: int, is_admin: bool
    ) -> None:
        if is_admin:
            return
        user = await self.users.get_by_discord_id(discord_user_id)
        if user is None or user.id != watch.added_by_user_id:
            raise PermissionDenied("only the watch owner or an admin may do this")
