from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_discord_id(self, discord_id: int) -> User | None:
        stmt = select(User).where(User.discord_id == discord_id, User.deleted_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(
        self,
        *,
        discord_id: int,
        discord_username: str | None = None,
        discord_avatar: str | None = None,
    ) -> User:
        user = User(
            discord_id=discord_id,
            discord_username=discord_username,
            discord_avatar=discord_avatar,
        )
        self.session.add(user)
        await self.session.flush()
        return user
