from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_event import AlertEvent
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.models.server import Server
from app.models.user import User
from app.models.watch import Watch
from app.repositories.alert_repo import AlertEventRepository
from app.repositories.price_repo import PriceSnapshotRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.server_repo import ServerRepository
from app.repositories.watch_repo import WatchRepository
from app.services.access_control import AccessControl
from app.services.errors import NotFound


@dataclass(frozen=True, slots=True)
class ServerSummary:
    server: Server
    is_admin: bool
    watch_count: int


@dataclass(frozen=True, slots=True)
class WatchDetail:
    watch: Watch
    product: Product
    server: Server
    alerts: list[AlertEvent]


@dataclass(frozen=True, slots=True)
class SnapshotRange:
    currency: str | None
    points: list[PriceSnapshot]


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.access = AccessControl(session)
        self.servers = ServerRepository(session)
        self.watches = WatchRepository(session)
        self.products = ProductRepository(session)
        self.alerts = AlertEventRepository(session)
        self.prices = PriceSnapshotRepository(session)

    async def list_servers(self, user: User) -> list[ServerSummary]:
        summaries: list[ServerSummary] = []
        for server, is_admin in await self.servers.list_for_user(user.id):
            count = await self.watches.count_active_for_server(server.id)
            summaries.append(ServerSummary(server=server, is_admin=is_admin, watch_count=count))
        return summaries

    async def get_server(self, user: User, guild_id: int) -> ServerSummary:
        membership = await self.access.assert_server_access(
            user_id=user.id, discord_id=user.discord_id, guild_id=guild_id, level="member"
        )
        server = await self.servers.get(membership.server_id)
        if server is None:
            raise NotFound("server not found")
        count = await self.watches.count_active_for_server(server.id)
        return ServerSummary(server=server, is_admin=membership.is_admin, watch_count=count)

    async def list_watches(self, user: User, guild_id: int) -> list[tuple[Watch, Product]]:
        membership = await self.access.assert_server_access(
            user_id=user.id, discord_id=user.discord_id, guild_id=guild_id, level="member"
        )
        return await self.watches.list_for_server_with_product(membership.server_id)

    async def get_watch(self, user: User, watch_id: uuid.UUID) -> WatchDetail:
        watch, product, server = await self._authorize_watch(user, watch_id)
        alerts = await self.alerts.list_for_watch(watch.id, limit=20)
        return WatchDetail(watch=watch, product=product, server=server, alerts=alerts)

    async def get_snapshots(
        self, user: User, watch_id: uuid.UUID, *, since: datetime, until: datetime
    ) -> SnapshotRange:
        _, product, _ = await self._authorize_watch(user, watch_id)
        points = await self.prices.range_for_product(product.id, since=since, until=until)
        return SnapshotRange(currency=product.currency, points=points)

    async def _authorize_watch(
        self, user: User, watch_id: uuid.UUID
    ) -> tuple[Watch, Product, Server]:
        watch = await self.watches.get(watch_id)
        if watch is None or watch.removed_at is not None:
            raise NotFound("watch not found")
        server = await self.servers.get(watch.server_id)
        if server is None:
            raise NotFound("watch not found")
        await self.access.assert_server_access(
            user_id=user.id,
            discord_id=user.discord_id,
            guild_id=server.guild_id,
            level="member",
        )
        product = await self.products.get(watch.product_id)
        if product is None:
            raise NotFound("watch not found")
        return watch, product, server
