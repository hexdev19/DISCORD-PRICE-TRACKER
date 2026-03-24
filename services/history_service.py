from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing
from db.repository import HistoryRepository, ListingRepository
from utils.chart_builder import build_sparkline
from utils.logger import get_logger

logger = get_logger(__name__)


class HistoryService:
	def __init__(self, listing_repo: type[ListingRepository], history_repo: type[HistoryRepository]) -> None:
		self._listing_repo = listing_repo
		self._history_repo = history_repo

	async def get_listing_by_url(self, session: AsyncSession, url: str) -> Listing | None:
		logger.info("history.get_listing_by_url.started", url=url)
		listing_repo = self._listing_repo(session)
		row = await listing_repo.get_by_url(url)
		logger.info("history.get_listing_by_url.completed", url=url, found=row is not None)
		return row

	async def get_listing_history(
		self,
		session: AsyncSession,
		listing_id: UUID,
		range_days: int | None,
		page: int,
		page_size: int = 10,
	) -> dict:
		logger.info("history.get_listing_history.started", listing_id=listing_id, range_days=range_days, page=page)
		history_repo = self._history_repo(session)
		rows = await history_repo.get_listing_history(
			listing_id=listing_id,
			range_days=range_days,
			page=page,
			page_size=page_size,
		)
		stats = await history_repo.get_stats(listing_id=listing_id, range_days=range_days)
		prices = [entry.price for entry in reversed(rows)]
		sparkline = build_sparkline(prices)
		result = {
			"rows": rows,
			"stats": stats,
			"sparkline": sparkline,
		}
		logger.info("history.get_listing_history.completed", listing_id=listing_id, rows=len(rows))
		return result

	async def get_product_history(self, session: AsyncSession, product_id: UUID, range_days: int | None) -> dict:
		logger.info("history.get_product_history.started", product_id=product_id, range_days=range_days)
		listing_repo = self._listing_repo(session)
		history_repo = self._history_repo(session)

		listings = await listing_repo.get_product_listings(product_id)
		listing_ids = [listing.id for listing in listings]
		range_stats_map = await history_repo.get_stats_bulk(listing_ids=listing_ids, range_days=range_days)
		all_time_stats_map = await history_repo.get_stats_bulk(listing_ids=listing_ids, range_days=None)
		per_store: dict[str, dict] = {}
		best_price_ever: Decimal | None = None

		for listing in listings:
			stats = range_stats_map.get(listing.id, {"min": None, "max": None, "avg": None})
			all_time_stats = all_time_stats_map.get(listing.id, {"min": None, "max": None, "avg": None})
			store_key = str(listing.store_id)
			entry = per_store.get(store_key)
			if entry is None:
				entry = {
					"store_id": listing.store_id,
					"currency": listing.currency,
					"min": stats.get("min"),
					"max": stats.get("max"),
					"avg_total": stats.get("avg") or Decimal("0"),
					"avg_count": 1 if stats.get("avg") is not None else 0,
					"listing_count": 1,
				}
				per_store[store_key] = entry
			else:
				entry["listing_count"] += 1
				if entry["min"] is None or (stats.get("min") is not None and stats["min"] < entry["min"]):
					entry["min"] = stats["min"]
				if entry["max"] is None or (stats.get("max") is not None and stats["max"] > entry["max"]):
					entry["max"] = stats["max"]
				if stats.get("avg") is not None:
					entry["avg_total"] += stats["avg"]
					entry["avg_count"] += 1

			if all_time_stats.get("min") is not None and (
				best_price_ever is None or all_time_stats["min"] < best_price_ever
			):
				best_price_ever = all_time_stats["min"]

		store_stats: list[dict] = []
		for data in per_store.values():
			avg_count = data.pop("avg_count")
			avg_total = data.pop("avg_total")
			data["avg"] = (avg_total / avg_count) if avg_count > 0 else None
			store_stats.append(data)

		result = {
			"stores": store_stats,
			"best_price_ever": best_price_ever,
		}
		logger.info("history.get_product_history.completed", product_id=product_id, stores=len(store_stats))
		return result
