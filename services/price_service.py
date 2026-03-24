from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing, Product
from db.repository import ListingRepository, ProductRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class PriceService:
	def __init__(self, product_repo: type[ProductRepository], listing_repo: type[ListingRepository]) -> None:
		self._product_repo = product_repo
		self._listing_repo = listing_repo

	async def get_comparison(self, session: AsyncSession, product_id: UUID) -> list[Listing]:
		logger.info("price.get_comparison.started", product_id=product_id)
		listing_repo = self._listing_repo(session)
		rows = await listing_repo.get_product_listings_scoped(product_id)
		logger.info("price.get_comparison.completed", product_id=product_id, rows=len(rows))
		return rows

	async def search_products(self, session: AsyncSession, discord_user_id: str, query: str) -> list[Product]:
		logger.info("price.search_products.started", discord_user_id=discord_user_id, query=query)
		product_repo = self._product_repo(session)
		rows = await product_repo.search_user_products(discord_user_id=discord_user_id, query=query, limit=25)
		logger.info("price.search_products.completed", discord_user_id=discord_user_id, rows=len(rows))
		return rows
