from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import ServerMembership
from app.models.server import Server


class ServerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, server_id: uuid.UUID) -> Server | None:
        return await self.session.get(Server, server_id)

    async def list_for_user(self, user_id: uuid.UUID) -> list[tuple[Server, bool]]:
        stmt = (
            select(Server, ServerMembership.is_admin)
            .join(ServerMembership, ServerMembership.server_id == Server.id)
            .where(ServerMembership.user_id == user_id, Server.is_active.is_(True))
            .order_by(Server.name)
        )
        rows = (await self.session.execute(stmt)).all()
        return [(server, is_admin) for server, is_admin in rows]

    async def get_by_guild_id(self, guild_id: int) -> Server | None:
        stmt = select(Server).where(Server.guild_id == guild_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, guild_id: int, name: str | None = None) -> Server:
        server = Server(guild_id=guild_id, name=name)
        self.session.add(server)
        await self.session.flush()
        return server
