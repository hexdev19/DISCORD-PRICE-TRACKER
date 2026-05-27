"""End-to-end worker pipeline: scrape → snapshot → alert evaluate → dispatch.

Exercises the full chain without invoking Celery itself. Discord is stubbed
via httpx MockTransport; the scraper router is replaced with a fake that
returns scripted ``ScrapeResult`` instances.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.limits import PRICE_HISTORY_DAYS
from app.models.price_snapshot import PriceSnapshot
from app.repositories.alert_repo import AlertEventRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.watch_repo import WatchRepository
from app.scraper.schemas import ScrapeResult
from app.services import queue
from app.services.alert_service import AlertService
from app.services.cooldown import InMemoryCooldownStore
from app.services.price_service import PriceService
from app.services.server_service import ServerService
from app.services.user_service import UserService
from app.services.watch_service import WatchService
from app.workers.discord_dispatcher import DiscordDispatcher
from app.workers.tasks.alert import _dispatch
from app.workers.tasks.maintenance import _prune_snapshots

pytestmark = pytest.mark.integration


class _RecordingQueue:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list, str]] = []

    def send_task(self, name: str, *, args: list, queue: str) -> None:
        self.calls.append((name, args, queue))


@pytest.fixture(autouse=True)
def _wire_queue() -> _RecordingQueue:
    fake = _RecordingQueue()
    queue.configure(fake)
    return fake


async def test_scrape_to_dispatch_full_chain(session: AsyncSession) -> None:
    await UserService(session).upsert_from_discord(discord_id=50001)
    server = await ServerService(session).upsert_from_discord(guild_id=60001)
    server.default_alert_channel_id = 999_111
    await session.commit()

    watch = await WatchService(session).add_watch(
        guild_id=60001,
        discord_user_id=50001,
        raw_url="https://example.com/p/chain",
    )
    await session.commit()

    pid = watch.product_id

    await PriceService(session).record_snapshot(
        pid,
        ScrapeResult(
            status="ok", tier_used=1, price=Decimal("100"), currency="USD", in_stock=True
        ),
    )
    await session.commit()

    second = await PriceService(session).record_snapshot(
        pid,
        ScrapeResult(
            status="ok", tier_used=1, price=Decimal("70"), currency="USD", in_stock=True
        ),
    )
    await session.commit()

    events = await AlertService(session, cooldowns=InMemoryCooldownStore()).evaluate(
        pid, second
    )
    await session.commit()
    assert [e.rule_type for e in events] == ["drop"]
    event_id = events[0].id

    sent: list[httpx.Request] = []

    async def handler(req: httpx.Request) -> httpx.Response:
        sent.append(req)
        return httpx.Response(204)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        outcome = await _dispatch(event_id, dispatcher=DiscordDispatcher(client=client))

    assert outcome is not None
    assert outcome.status == "delivered"
    assert len(sent) == 1
    assert "/channels/999111/messages" in str(sent[0].url)

    refreshed = await AlertEventRepository(session).get(event_id)
    assert refreshed is not None
    assert refreshed.delivery_status == "delivered"
    assert refreshed.delivered_at is not None


async def test_dispatch_marks_failed_when_channel_missing(session: AsyncSession) -> None:
    await UserService(session).upsert_from_discord(discord_id=50002)
    await ServerService(session).upsert_from_discord(guild_id=60002)
    await session.commit()

    watch = await WatchService(session).add_watch(
        guild_id=60002,
        discord_user_id=50002,
        raw_url="https://example.com/p/no-channel",
    )
    await session.commit()

    event = await AlertEventRepository(session).create(
        watch_id=watch.id,
        rule_type="drop",
        previous_price=Decimal("100"),
        new_price=Decimal("80"),
        previous_in_stock=True,
        new_in_stock=True,
        payload={"rule": "drop"},
    )
    await session.commit()

    outcome = await _dispatch(event.id)
    assert outcome is not None
    assert outcome.status == "channel_gone"
    refreshed = await AlertEventRepository(session).get(event.id)
    assert refreshed is not None
    assert refreshed.delivery_status == "failed"
    assert refreshed.last_error == "channel_missing"


async def test_prune_snapshots_removes_old_rows(session: AsyncSession) -> None:
    product = await ProductRepository(session).create(
        source_url="https://example.com/p/prune", domain="example.com"
    )
    await session.commit()

    cutoff = datetime.now(timezone.utc) - timedelta(days=PRICE_HISTORY_DAYS + 5)
    fresh = datetime.now(timezone.utc) - timedelta(days=1)

    for observed_at in (cutoff, cutoff, fresh):
        session.add(
            PriceSnapshot(
                product_id=product.id,
                observed_at=observed_at,
                price=Decimal("10"),
                currency="USD",
                in_stock=True,
                source_tier=1,
                scrape_status="ok",
            )
        )
    await session.commit()

    removed = await _prune_snapshots()
    assert removed == 2

    remaining = await PriceSnapshotRepository_count_for_product(session, product.id)
    assert remaining == 1


async def PriceSnapshotRepository_count_for_product(
    session: AsyncSession, product_id: uuid.UUID
) -> int:
    from sqlalchemy import func, select

    stmt = (
        select(func.count())
        .select_from(PriceSnapshot)
        .where(PriceSnapshot.product_id == product_id)
    )
    return int((await session.execute(stmt)).scalar_one())
