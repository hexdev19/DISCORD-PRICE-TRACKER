from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot


class PriceSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(
        self,
        *,
        product_id: uuid.UUID,
        observed_at: datetime,
        price: Decimal | None,
        currency: str | None,
        in_stock: bool | None,
        source_tier: int,
        scrape_status: str,
        confidence: float | None = None,
    ) -> PriceSnapshot:
        snapshot = PriceSnapshot(
            product_id=product_id,
            observed_at=observed_at,
            price=price,
            currency=currency,
            in_stock=in_stock,
            source_tier=source_tier,
            scrape_status=scrape_status,
            confidence=confidence,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def latest_for_product(
        self, product_id: uuid.UUID, *, limit: int = 1
    ) -> list[PriceSnapshot]:
        stmt = (
            select(PriceSnapshot)
            .where(PriceSnapshot.product_id == product_id)
            .order_by(desc(PriceSnapshot.observed_at))
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars())

    async def range_for_product(
        self, product_id: uuid.UUID, *, since: datetime, until: datetime
    ) -> list[PriceSnapshot]:
        stmt = (
            select(PriceSnapshot)
            .where(
                PriceSnapshot.product_id == product_id,
                PriceSnapshot.observed_at >= since,
                PriceSnapshot.observed_at <= until,
            )
            .order_by(asc(PriceSnapshot.observed_at))
        )
        return list((await self.session.execute(stmt)).scalars())
