from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.price_repo import PriceSnapshotRepository
from app.scraper.schemas import ScrapeResult
from app.services import queue
from app.services.alert_service import AlertService
from app.services.cooldown import InMemoryCooldownStore
from app.services.price_service import PriceService
from app.services.server_service import ServerService
from app.services.user_service import UserService
from app.services.watch_service import WatchService

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


async def _seed(
    session: AsyncSession, *, url: str, rules: dict
) -> tuple[int, int, str]:
    guild_id = 9001 + abs(hash(url)) % 1000
    discord_id = 8001 + abs(hash(url)) % 1000
    await UserService(session).upsert_from_discord(discord_id=discord_id)
    await ServerService(session).upsert_from_discord(guild_id=guild_id)
    await session.commit()

    watch = await WatchService(session).add_watch(
        guild_id=guild_id, discord_user_id=discord_id, raw_url=url
    )
    watch.alert_rules = rules
    await session.commit()
    return guild_id, discord_id, str(watch.product_id)


async def _append(
    session: AsyncSession,
    product_id: str,
    *,
    price: Decimal | None,
    in_stock: bool | None,
) -> int:
    import uuid

    result = ScrapeResult(
        status="ok",
        tier_used=1,
        price=price,
        currency="USD",
        in_stock=in_stock,
    )
    snap = await PriceService(session).record_snapshot(uuid.UUID(product_id), result)
    await session.commit()
    return snap.id


async def test_drop_fires_on_price_decrease(
    session: AsyncSession, _wire_queue: _RecordingQueue
) -> None:
    import uuid

    _, _, pid = await _seed(
        session, url="https://example.com/p/drop", rules={"drop": True}
    )
    await _append(session, pid, price=Decimal("100"), in_stock=True)
    new_id = await _append(session, pid, price=Decimal("80"), in_stock=True)

    snap = await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1)
    new = next(s for s in snap if s.id == new_id)
    cooldowns = InMemoryCooldownStore()
    svc = AlertService(session, cooldowns=cooldowns)

    events = await svc.evaluate(uuid.UUID(pid), new)
    await session.commit()
    assert len(events) == 1
    assert events[0].rule_type == "drop"
    assert _wire_queue.calls == [("alert.dispatch", [events[0].id], "alert")]


async def test_drop_skipped_when_price_equal_or_higher(session: AsyncSession) -> None:
    import uuid

    _, _, pid = await _seed(
        session, url="https://example.com/p/nodrop", rules={"drop": True}
    )
    await _append(session, pid, price=Decimal("50"), in_stock=True)
    new_id = await _append(session, pid, price=Decimal("60"), in_stock=True)

    snap = (await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1))[0]
    assert snap.id == new_id
    events = await AlertService(session).evaluate(uuid.UUID(pid), snap)
    assert events == []


async def test_threshold_fires_when_below(session: AsyncSession) -> None:
    import uuid

    _, _, pid = await _seed(
        session,
        url="https://example.com/p/thr",
        rules={"threshold": "75.00"},
    )
    await _append(session, pid, price=Decimal("100"), in_stock=True)
    new = await _append(session, pid, price=Decimal("70"), in_stock=True)
    snap = (await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1))[0]
    assert snap.id == new

    events = await AlertService(session, cooldowns=InMemoryCooldownStore()).evaluate(
        uuid.UUID(pid), snap
    )
    await session.commit()
    assert [e.rule_type for e in events] == ["threshold"]


async def test_restock_fires(session: AsyncSession) -> None:
    import uuid

    _, _, pid = await _seed(
        session, url="https://example.com/p/restock", rules={"restock": True}
    )
    await _append(session, pid, price=Decimal("10"), in_stock=False)
    new = await _append(session, pid, price=Decimal("10"), in_stock=True)
    snap = (await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1))[0]
    assert snap.id == new

    events = await AlertService(session, cooldowns=InMemoryCooldownStore()).evaluate(
        uuid.UUID(pid), snap
    )
    await session.commit()
    assert [e.rule_type for e in events] == ["restock"]


async def test_cooldown_suppresses_repeat_alert(session: AsyncSession) -> None:
    import uuid

    _, _, pid = await _seed(
        session, url="https://example.com/p/cool", rules={"drop": True}
    )
    await _append(session, pid, price=Decimal("100"), in_stock=True)
    new = await _append(session, pid, price=Decimal("80"), in_stock=True)
    snap = (await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1))[0]
    assert snap.id == new

    cooldowns = InMemoryCooldownStore()
    svc = AlertService(session, cooldowns=cooldowns)
    first = await svc.evaluate(uuid.UUID(pid), snap)
    await session.commit()
    assert len(first) == 1

    again = await _append(session, pid, price=Decimal("70"), in_stock=True)
    again_snap = (
        await PriceSnapshotRepository(session).latest_for_product(uuid.UUID(pid), limit=1)
    )[0]
    assert again_snap.id == again
    second = await svc.evaluate(uuid.UUID(pid), again_snap)
    assert second == []
