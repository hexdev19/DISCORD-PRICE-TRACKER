from __future__ import annotations

import asyncio
from uuid import UUID

from celery import Task

from db.repository import ListingRepository, ProductRepository, WatchRepository
from db.session import AsyncSessionFactory
from services import AlertService
from tasks.celery_app import celery_app
from utils import embed_builder
from utils.logger import get_logger


logger = get_logger(__name__)

alert_service = AlertService(WatchRepository)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def dispatch_alerts(self: Task, listing_id: str, change_type: str) -> None:
	logger.info("alerts.dispatch.started", listing_id=listing_id, change_type=change_type)
	try:
		listing_uuid = UUID(listing_id)

		async def run() -> None:
			bot = celery_app.conf.get("bot")
			if bot is None:
				logger.warning("alerts.dispatch.bot_unavailable", listing_id=listing_id)
				return

			async with AsyncSessionFactory() as session:
				listing_repo = ListingRepository(session)
				product_repo = ProductRepository(session)

				watches = await alert_service.get_watches_for_listing(session=session, listing_id=listing_uuid)
				listing = await listing_repo.get_by_id(listing_uuid)
				if listing is None:
					logger.warning("alerts.dispatch.listing_not_found", listing_id=listing_id)
					return

				product = await product_repo.get_by_id(listing.product_id)
				if product is None:
					logger.warning("alerts.dispatch.product_not_found", listing_id=listing_id)
					return

				for watch in watches:
					if not alert_service.should_alert(watch, change_type):
						continue
					user = bot.get_user(int(watch.discord_user_id))
					if user is None:
						user = await bot.fetch_user(int(watch.discord_user_id))
					if user is None:
						continue
						embed = embed_builder.alert_embed(listing, product, change_type)
					await user.send(embed=embed)

		asyncio.run(run())
		logger.info("alerts.dispatch.completed", listing_id=listing_id, change_type=change_type)
		except Exception as exc:
		logger.exception("alerts.dispatch.failed", listing_id=listing_id, change_type=change_type)
			raise self.retry(exc=exc, countdown=2 ** self.request.retries)

