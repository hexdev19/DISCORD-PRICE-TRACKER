from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select

from app.config.limits import CHECK_CADENCE_SECONDS
from app.db.session import SessionFactory
from app.models.product import Product
from app.models.watch import Watch
from app.repositories.price_repo import PriceSnapshotRepository
from app.scraper.circuit import RedisCircuitBreaker
from app.scraper.router import RouterDeps, TierRouter
from app.services import queue
from app.services.alert_service import AlertService
from app.services.cooldown import RedisCooldownStore
from app.services.price_service import PriceService
from app.utils.logger import get_logger
from app.workers.locks import ScrapeLock
from app.workers.redis import async_client

log = get_logger(__name__)


async def _tick() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=CHECK_CADENCE_SECONDS)
    async with SessionFactory() as session:
        stmt = (
            select(Product.id)
            .join(Watch, Watch.product_id == Product.id)
            .where(
                Watch.is_active.is_(True),
                Watch.paused_at.is_(None),
                Watch.removed_at.is_(None),
            )
            .where(
                (Product.last_scraped_at.is_(None)) | (Product.last_scraped_at <= cutoff)
            )
            .distinct()
        )
        rows = list((await session.execute(stmt)).scalars().all())

    for product_id in rows:
        await asyncio.sleep(random.uniform(0, 0.05))  # noqa: S311 — jitter only
        queue.enqueue_scrape(product_id)
    log.info("scrape.tick", enqueued=len(rows))
    return len(rows)


async def _scrape_product(
    product_id: str,
    *,
    router: TierRouter | None = None,
) -> None:
    pid = uuid.UUID(product_id)
    redis = async_client()
    lock = ScrapeLock(redis)
    token = await lock.acquire(pid)
    if token is None:
        log.info("scrape.skipped_locked", product_id=str(pid))
        return

    try:
        async with SessionFactory() as session:
            product = await session.get(Product, pid)
            if product is None:
                log.warning("scrape.unknown_product", product_id=str(pid))
                return

            chosen_router = router or _default_router()
            result = await chosen_router.scrape(
                product.source_url, region_hint=product.region
            )
            snapshot = await PriceService(session).record_snapshot(pid, result)
            await session.commit()
            snapshot_id = snapshot.id
            scrape_status = result.status
            tier = result.tier_used

        log.info(
            "scrape.recorded",
            product_id=str(pid),
            status=scrape_status,
            tier=tier,
        )

        if scrape_status in ("ok", "partial"):
            await _evaluate(pid, snapshot_id)
    finally:
        await lock.release(pid, token)


async def _evaluate(product_id: uuid.UUID, snapshot_id: int) -> None:
    cooldowns = RedisCooldownStore(async_client())
    async with SessionFactory() as session:
        snapshot = next(
            (
                s
                for s in await PriceSnapshotRepository(session).latest_for_product(
                    product_id, limit=5
                )
                if s.id == snapshot_id
            ),
            None,
        )
        if snapshot is None:
            return
        events = await AlertService(session, cooldowns=cooldowns).evaluate(
            product_id, snapshot
        )
        await session.commit()
    log.info(
        "alert.evaluated",
        product_id=str(product_id),
        fired=[e.rule_type for e in events],
    )


def _default_router() -> TierRouter:
    from app.scraper.browser import get_browser_session
    from app.scraper.fetcher import fetch_html

    session = get_browser_session()
    return TierRouter(
        RouterDeps(
            fetch_html=fetch_html,
            render_page=session.render,
            circuit=RedisCircuitBreaker(async_client()),
        )
    )


@shared_task(name="scrape.tick")
def tick_task() -> int:
    return asyncio.run(_tick())


@shared_task(
    name="scrape.product",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=3,
)
def scrape_product_task(product_id: str) -> None:
    asyncio.run(_scrape_product(product_id))
