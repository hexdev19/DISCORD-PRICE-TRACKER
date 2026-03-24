from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import UUID

from celery import Task

from db.repository import HistoryRepository, ListingRepository, ProductRepository, StoreRepository, WatchRepository
from db.session import AsyncSessionFactory
from services.product_service import ProductService
from tasks.alert import dispatch_alerts
from tasks.celery_app import celery_app
from utils import embed_builder
from utils.logger import get_logger


logger = get_logger(__name__)

product_service = ProductService(StoreRepository, ProductRepository, ListingRepository, WatchRepository, HistoryRepository)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def scrape_listing(self: Task, listing_id: str) -> None:
	logger.info("scrape_listing.started", listing_id=listing_id)
	try:
		listing_uuid = UUID(listing_id)

		async def run() -> None:
			async with AsyncSessionFactory() as session:
				listing_repo = ListingRepository(session)
				history_repo = HistoryRepository(session)

				listing = await listing_repo.get_by_id(listing_uuid)
				if listing is None:
					logger.warning("scrape_listing.listing_not_found", listing_id=listing_id)
					return

				scraped = await scrape_service.scrape(listing.url)
				price_delta = scraped.price - listing.current_price
				delta_pct = None
				if listing.current_price != 0:
					delta_pct = (price_delta / listing.current_price) * Decimal("100")

				if listing.in_stock != scraped.in_stock:
					change_type = "restock" if scraped.in_stock else "out_of_stock"
				elif scraped.price < listing.current_price:
					change_type = "price_drop"
				elif scraped.price > listing.current_price:
					change_type = "price_rise"
				else:
					change_type = "no_change"

				await listing_repo.update_price(listing_uuid, scraped.price, scraped.in_stock)
				await history_repo.append(
					listing_id=listing_uuid,
					price=scraped.price,
					currency=scraped.currency,
					in_stock=scraped.in_stock,
					price_delta=price_delta,
					delta_pct=delta_pct,
					change_type=change_type,
				)
				await session.commit()

				if change_type != "no_change":
					dispatch_alerts.delay(listing_id, change_type)

		asyncio.run(run())
		logger.info("scrape_listing.completed", listing_id=listing_id)
	except Exception as exc:
		logger.exception("scrape_listing.failed", listing_id=listing_id)
		raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def scrape_batch(self: Task, urls: list[str], channel_id: int, message_id: int) -> None:
	logger.info("scrape_batch.started", url_count=len(urls), channel_id=channel_id, message_id=message_id)
	try:
		async def run() -> None:
			results = []
			async with AsyncSessionFactory() as session:
				for url in urls:
					listing = await product_service.resolve_listing(session=session, url=url)
					results.append(listing)
				await session.commit()

			bot = celery_app.conf.get("bot")
			if bot is None:
				logger.warning("scrape_batch.bot_unavailable", channel_id=channel_id, message_id=message_id)
				return

			channel = bot.get_channel(channel_id)
			if channel is None:
				channel = await bot.fetch_channel(channel_id)

			message = await channel.fetch_message(message_id)
			await message.edit(embed=embed_builder.comparison_embed(results))

		asyncio.run(run())
		logger.info("scrape_batch.completed", url_count=len(urls), channel_id=channel_id, message_id=message_id)
	except Exception as exc:
		logger.exception("scrape_batch.failed", channel_id=channel_id, message_id=message_id)
		raise self.retry(exc=exc, countdown=2 ** self.request.retries)

