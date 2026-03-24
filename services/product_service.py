from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from db.models import Listing, UserWatch
from db.repository import HistoryRepository, ListingRepository, ProductRepository, StoreRepository, WatchRepository
from scraper.scrape_service import ScrapeService, build_scrape_service
from services import AppError
from utils.logger import get_logger
from utils.url_utils import extract_domain


logger = get_logger(__name__)

_default_scrape_service: ScrapeService = build_scrape_service(settings)


class DuplicateWatchError(AppError):
	def __init__(self, discord_user_id: str, listing_id: UUID) -> None:
		super().__init__("User is already tracking this listing")
		self.discord_user_id = discord_user_id
		self.listing_id = listing_id


class WatchNotFoundError(AppError):
	def __init__(self, discord_user_id: str, listing_id: UUID) -> None:
		super().__init__("Watch not found")
		self.discord_user_id = discord_user_id
		self.listing_id = listing_id


class ProductService:
	def __init__(
		self,
		store_repo: type[StoreRepository],
		product_repo: type[ProductRepository],
		listing_repo: type[ListingRepository],
		watch_repo: type[WatchRepository],
		history_repo: type[HistoryRepository] = HistoryRepository,
		scrape_service: ScrapeService | None = None,
	) -> None:
		self._store_repo = store_repo
		self._product_repo = product_repo
		self._listing_repo = listing_repo
		self._watch_repo = watch_repo
		self._history_repo = history_repo
		self._scrape_service = scrape_service or _default_scrape_service

	async def track_url(self, session: AsyncSession, url: str, discord_user_id: str | None = None) -> Listing:
		logger.info("product.track_url.started", url=url, discord_user_id=discord_user_id)

		store_repo = self._store_repo(session)
		product_repo = self._product_repo(session)
		listing_repo = self._listing_repo(session)
		watch_repo = self._watch_repo(session)
		history_repo = self._history_repo(session)

		scraped = await self._scrape_service.scrape(url)
		domain = extract_domain(url)

		store = await store_repo.get_or_create(name=scraped.store_name, domain=domain, country=None)

		product = await product_repo.find_similar(scraped.title)
		if product is None:
			product = await product_repo.create(canonical_name=scraped.title, image_url=scraped.image_url)

		listing = await listing_repo.get_by_url(url)
		if listing is None:
			listing = await listing_repo.create(
				product_id=product.id,
				store_id=store.id,
				url=url,
				title=scraped.title,
				price=scraped.price,
				currency=scraped.currency,
				in_stock=scraped.in_stock,
			)
		else:
			await listing_repo.update_price(listing.id, scraped.price, scraped.in_stock)

		if discord_user_id is not None:
			existing_watch = await watch_repo.get_by_user_and_listing(
				discord_user_id=discord_user_id,
				listing_id=listing.id,
			)
			if existing_watch is not None:
				raise DuplicateWatchError(discord_user_id=discord_user_id, listing_id=listing.id)

			await watch_repo.create(discord_user_id=discord_user_id, listing_id=listing.id)

		latest_history = await history_repo.get_latest(listing.id)
		if latest_history is None:
			await history_repo.append(
				listing_id=listing.id,
				price=listing.current_price,
				currency=listing.currency,
				in_stock=listing.in_stock,
				price_delta=None,
				delta_pct=None,
				change_type="no_change",
			)

		logger.info("product.track_url.completed", url=url, discord_user_id=discord_user_id, listing_id=listing.id)
		return listing

	async def untrack(self, session: AsyncSession, listing_id: UUID, discord_user_id: str) -> None:
		logger.info("product.untrack.started", listing_id=listing_id, discord_user_id=discord_user_id)
		watch_repo = self._watch_repo(session)
		deleted = await watch_repo.delete(discord_user_id=discord_user_id, listing_id=listing_id)
		if not deleted:
			raise WatchNotFoundError(discord_user_id=discord_user_id, listing_id=listing_id)
		logger.info("product.untrack.completed", listing_id=listing_id, discord_user_id=discord_user_id)

	async def get_user_watches(
		self,
		session: AsyncSession,
		discord_user_id: str,
		query: str | None,
	) -> list[UserWatch]:
		watch_repo = self._watch_repo(session)
		return await watch_repo.get_user_watches(discord_user_id=discord_user_id, query=query)
