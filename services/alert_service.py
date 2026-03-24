from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import UserWatch
from db.repository import WatchRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class AlertService:
	def __init__(self, watch_repo: type[WatchRepository]) -> None:
		self._watch_repo = watch_repo

	async def get_watches_for_listing(self, session: AsyncSession, listing_id: UUID) -> list[UserWatch]:
		logger.info("alert.get_watches_for_listing.started", listing_id=listing_id)
		watch_repo = self._watch_repo(session)
		rows = await watch_repo.get_for_listing(listing_id)
		logger.info("alert.get_watches_for_listing.completed", listing_id=listing_id, rows=len(rows))
		return rows

	def should_alert(self, watch: UserWatch, change_type: str) -> bool:
		if change_type == "price_drop":
			return watch.alert_on_drop
		if change_type == "price_rise":
			return watch.alert_on_rise
		if change_type in {"restock", "out_of_stock"}:
			return watch.alert_on_stock
		return False
