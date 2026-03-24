from __future__ import annotations

import asyncio

from db.repository import ListingRepository
from db.session import AsyncSessionFactory
from tasks.celery_app import celery_app
from tasks.scrape_job import scrape_listing
from utils.logger import get_logger


logger = get_logger(__name__)


@celery_app.task
def monitor_all_listings() -> None:
	async def run() -> list[str]:
		async with AsyncSessionFactory() as session:
			listing_repo = ListingRepository(session)
			listing_ids = await listing_repo.get_distinct_watched_listing_ids()
			return [str(item) for item in listing_ids]

	logger.info("monitor.started")
	listing_ids = asyncio.run(run())
	for listing_id in listing_ids:
		scrape_listing.delay(listing_id)
	logger.info("monitor.completed", listings=len(listing_ids))

