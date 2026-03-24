from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Literal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ListingHistory

ChangeType = Literal["price_drop", "price_rise", "restock", "out_of_stock", "no_change"]


class HistoryRepository:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_listing_history(
		self,
		listing_id: UUID,
		range_days: int | None,
		page: int,
		page_size: int = 10,
	) -> list[ListingHistory]:
		stmt = select(ListingHistory).where(ListingHistory.listing_id == listing_id)
		if range_days is not None:
			since = datetime.utcnow() - timedelta(days=range_days)
			stmt = stmt.where(ListingHistory.recorded_at >= since)
		safe_page = max(page, 1)
		stmt = (
			stmt.order_by(ListingHistory.recorded_at.desc())
			.offset((safe_page - 1) * page_size)
			.limit(page_size)
		)
		result = await self.session.execute(stmt)
		return list(result.scalars().all())

	async def get_latest(self, listing_id: UUID) -> ListingHistory | None:
		stmt = (
			select(ListingHistory)
			.where(ListingHistory.listing_id == listing_id)
			.order_by(ListingHistory.recorded_at.desc())
			.limit(1)
		)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_stats(self, listing_id: UUID, range_days: int | None) -> dict:
		stmt = select(
			func.min(ListingHistory.price).label("min"),
			func.max(ListingHistory.price).label("max"),
			func.avg(ListingHistory.price).label("avg"),
		).where(ListingHistory.listing_id == listing_id)
		if range_days is not None:
			since = datetime.utcnow() - timedelta(days=range_days)
			stmt = stmt.where(ListingHistory.recorded_at >= since)
		row = (await self.session.execute(stmt)).one()
		return {
			"min": row.min,
			"max": row.max,
			"avg": row.avg,
		}

	async def append(
		self,
		listing_id: UUID,
		price: Decimal,
		currency: str,
		in_stock: bool,
		price_delta: Decimal | None,
		delta_pct: Decimal | None,
		change_type: ChangeType,
	) -> ListingHistory:
		history_item = ListingHistory(
			listing_id=listing_id,
			price=price,
			currency=currency,
			in_stock=in_stock,
			price_delta=price_delta,
			delta_pct=delta_pct,
			change_type=change_type,
		)
		self.session.add(history_item)
		await self.session.flush()
		return history_item

