from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_event import AlertEvent


class AlertEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, alert_id: int) -> AlertEvent | None:
        return await self.session.get(AlertEvent, alert_id)

    async def create(
        self,
        *,
        watch_id: uuid.UUID,
        rule_type: str,
        previous_price: Decimal | None,
        new_price: Decimal | None,
        previous_in_stock: bool | None,
        new_in_stock: bool | None,
        payload: dict[str, Any],
    ) -> AlertEvent:
        event = AlertEvent(
            watch_id=watch_id,
            rule_type=rule_type,
            previous_price=previous_price,
            new_price=new_price,
            previous_in_stock=previous_in_stock,
            new_in_stock=new_in_stock,
            payload=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_for_watch(
        self, watch_id: uuid.UUID, *, limit: int = 50
    ) -> list[AlertEvent]:
        stmt = (
            select(AlertEvent)
            .where(AlertEvent.watch_id == watch_id)
            .order_by(desc(AlertEvent.triggered_at))
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars())

    async def mark_delivered(self, alert_id: int) -> bool:
        """CASE: pending → delivered. Returns True if the row was updated."""
        stmt = (
            update(AlertEvent)
            .where(AlertEvent.id == alert_id, AlertEvent.delivery_status == "pending")
            .values(delivery_status="delivered", delivered_at=_now())
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0


def _now() -> Any:
    from sqlalchemy import func
    return func.now()
