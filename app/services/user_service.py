from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.user_repo import UserRepository
from app.services.errors import NotFound


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.audit = AuditLogRepository(session)

    async def upsert_from_discord(
        self,
        *,
        discord_id: int,
        discord_username: str | None = None,
        discord_avatar: str | None = None,
    ) -> User:
        user = await self.users.get_by_discord_id(discord_id)
        if user is None:
            user = await self.users.create(
                discord_id=discord_id,
                discord_username=discord_username,
                discord_avatar=discord_avatar,
            )
            await self.audit.record(
                action="user.created",
                actor_type="user",
                actor_id=str(discord_id),
                target_type="user",
                target_id=str(user.id),
            )
            return user
        if discord_username is not None:
            user.discord_username = discord_username
        if discord_avatar is not None:
            user.discord_avatar = discord_avatar
        await self.session.flush()
        return user

    async def soft_delete(self, user_id: uuid.UUID, *, actor_id: str | None = None) -> None:
        user = await self.users.get(user_id)
        if user is None or user.deleted_at is not None:
            raise NotFound("user not found")
        user.deleted_at = datetime.now(timezone.utc)
        await self.audit.record(
            action="account.deleted",
            actor_type="user",
            actor_id=actor_id or str(user.discord_id),
            target_type="user",
            target_id=str(user.id),
        )
