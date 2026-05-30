from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.watch import Watch


class WatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, watch_id: uuid.UUID) -> Watch | None:
        return await self.session.get(Watch, watch_id)

    async def get_by_short_id(self, short_id: str) -> Watch | None:
        stmt = select(Watch).where(Watch.short_id == short_id, Watch.removed_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_server_and_product(
        self, server_id: uuid.UUID, product_id: uuid.UUID, *, include_removed: bool = False
    ) -> Watch | None:
        stmt = select(Watch).where(
            Watch.server_id == server_id,
            Watch.product_id == product_id,
        )
        if not include_removed:
            stmt = stmt.where(Watch.removed_at.is_(None))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_server(self, server_id: uuid.UUID) -> list[Watch]:
        stmt = select(Watch).where(Watch.server_id == server_id, Watch.removed_at.is_(None))
        return list((await self.session.execute(stmt)).scalars())

    async def list_for_server_with_product(
        self, server_id: uuid.UUID
    ) -> list[tuple[Watch, Product]]:
        stmt = (
            select(Watch, Product)
            .join(Product, Product.id == Watch.product_id)
            .where(Watch.server_id == server_id, Watch.removed_at.is_(None))
            .order_by(Watch.created_at.desc())
        )
        rows = (await self.session.execute(stmt)).all()
        return [(watch, product) for watch, product in rows]

    async def list_active_for_product(self, product_id: uuid.UUID) -> list[Watch]:
        stmt = select(Watch).where(
            Watch.product_id == product_id,
            Watch.is_active.is_(True),
            Watch.paused_at.is_(None),
            Watch.removed_at.is_(None),
        )
        return list((await self.session.execute(stmt)).scalars())

    async def count_active_for_server(self, server_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Watch)
            .where(Watch.server_id == server_id, Watch.removed_at.is_(None))
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_for_user_in_server(self, server_id: uuid.UUID, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Watch)
            .where(
                Watch.server_id == server_id,
                Watch.added_by_user_id == user_id,
                Watch.removed_at.is_(None),
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def create(
        self,
        *,
        server_id: uuid.UUID,
        added_by_user_id: uuid.UUID,
        product_id: uuid.UUID,
        alert_rules: dict[str, Any],
    ) -> Watch:
        watch = Watch(
            server_id=server_id,
            added_by_user_id=added_by_user_id,
            product_id=product_id,
            alert_rules=alert_rules,
        )
        self.session.add(watch)
        await self.session.flush()
        return watch
