from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.server import Server


class ServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, server_id: uuid.UUID) -> Server | None:
        return await self.session.get(Server, server_id)

    async def get_by_guild_id(self, guild_id: int) -> Server | None:
        stmt = select(Server).where(Server.guild_id == guild_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, guild_id: int, name: str | None = None) -> Server:
        server = Server(guild_id=guild_id, name=name)
        self.session.add(server)
        await self.session.flush()
        return server
