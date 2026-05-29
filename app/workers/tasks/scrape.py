from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select

from app.config.limits import CHECK_CADENCE_SECONDS
from app.models.product import Product
from app.models.watch import Watch
from app.repositories.price_repo import PriceSnapshotRepository
from app.scraper.browser import BrowserSession
from app.scraper.circuit import RedisCircuitBreaker
from app.scraper.fetcher import fetch_html
from app.scraper.router import RouterDeps, TierRouter
from app.services import queue
from app.services.alert_service import AlertService
from app.services.cooldown import RedisCooldownStore
from app.services.price_service import PriceService
from app.utils.logger import get_logger
from app.workers.locks import ScrapeLock
from app.workers.runtime import WorkerRuntime, worker_runtime

log = get_logger(__name__)


async def _tick() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=CHECK_CADENCE_SECONDS)
    async with worker_runtime() as runtime, runtime.session_factory() as session:
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
    async with worker_runtime() as runtime:
        lock = ScrapeLock(runtime.redis)
        token = await lock.acquire(pid)
        if token is None:
            log.info("scrape.skipped_locked", product_id=str(pid))
            return

        browser: BrowserSession | None = None
        try:
            async with runtime.session_factory() as session:
                product = await session.get(Product, pid)
                if product is None:
                    log.warning("scrape.unknown_product", product_id=str(pid))
                    return

                if router is None:
                    browser = BrowserSession()
                    chosen_router = _build_router(runtime, browser)
                else:
                    chosen_router = router
                result = await chosen_router.scrape(
                    product.source_url, region_hint=product.region
                )
                outcome = await PriceService(session).record_snapshot(pid, result)
                await session.commit()
                snapshot_id = outcome.snapshot.id
                scrape_status = result.status
                tier = result.tier_used

            log.info(
                "scrape.recorded",
                product_id=str(pid),
                status=scrape_status,
                tier=tier,
            )

            if scrape_status in ("ok", "partial"):
                await _evaluate(runtime, pid, snapshot_id)
        finally:
            if browser is not None:
                await browser.close()
            await lock.release(pid, token)


async def _evaluate(
    runtime: WorkerRuntime, product_id: uuid.UUID, snapshot_id: int
) -> None:
    cooldowns = RedisCooldownStore(runtime.redis)
    async with runtime.session_factory() as session:
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


def _build_router(runtime: WorkerRuntime, browser: BrowserSession) -> TierRouter:
    return TierRouter(
        RouterDeps(
            fetch_html=fetch_html,
            render_page=browser.render,
            circuit=RedisCircuitBreaker(runtime.redis),
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
