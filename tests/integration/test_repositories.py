"""Round-trip every repository against a real Postgres."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    AlertEventRepository,
    PriceSnapshotRepository,
    ProductRepository,
    ServerRepository,
    UserRepository,
    WatchRepository,
)

pytestmark = pytest.mark.integration


async def test_user_create_and_lookup(session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await repo.create(discord_id=10001, discord_username="alice")
    await session.commit()

    fetched = await repo.get_by_discord_id(10001)
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.discord_username == "alice"
    assert fetched.plan == "free"


async def test_server_create_and_lookup(session: AsyncSession) -> None:
    repo = ServerRepository(session)
    server = await repo.create(guild_id=20001, name="Test Guild")
    await session.commit()

    fetched = await repo.get_by_guild_id(20001)
    assert fetched is not None
    assert fetched.id == server.id
    assert fetched.is_active is True


async def test_product_create_and_update_last_scrape(session: AsyncSession) -> None:
    repo = ProductRepository(session)
    product = await repo.create(
        source_url="https://example.com/p/1", domain="example.com", region="US"
    )
    await session.commit()

    now = datetime.now(timezone.utc)
    await repo.update_last_scrape(
        product,
        observed_at=now,
        price=Decimal("99.99"),
        currency="USD",
        in_stock=True,
        status="ok",
        tier=1,
    )
    await session.commit()

    refreshed = await repo.get_by_source_url("https://example.com/p/1")
    assert refreshed is not None
    assert refreshed.last_known_price == Decimal("99.99")
    assert refreshed.last_scrape_status == "ok"
    assert refreshed.scrape_tier == 1


async def test_watch_lifecycle(session: AsyncSession) -> None:
    users = UserRepository(session)
    servers = ServerRepository(session)
    products = ProductRepository(session)
    watches = WatchRepository(session)

    user = await users.create(discord_id=10002)
    server = await servers.create(guild_id=20002)
    product = await products.create(source_url="https://example.com/p/2", domain="example.com")
    await session.commit()

    watch = await watches.create(
        server_id=server.id,
        added_by_user_id=user.id,
        product_id=product.id,
        alert_rules={"drop": True, "restock": True},
    )
    await session.commit()

    assert len(watch.short_id) == 8
    found_by_short = await watches.get_by_short_id(watch.short_id)
    assert found_by_short is not None and found_by_short.id == watch.id

    assert await watches.count_active_for_server(server.id) == 1
    assert await watches.count_for_user_in_server(server.id, user.id) == 1
    assert [w.id for w in await watches.list_active_for_product(product.id)] == [watch.id]


async def test_price_snapshot_append_and_latest(session: AsyncSession) -> None:
    products = ProductRepository(session)
    snapshots = PriceSnapshotRepository(session)

    product = await products.create(source_url="https://example.com/p/3", domain="example.com")
    await session.commit()

    now = datetime.now(timezone.utc)
    await snapshots.append(
        product_id=product.id,
        observed_at=now,
        price=Decimal("10.00"),
        currency="USD",
        in_stock=True,
        source_tier=1,
        scrape_status="ok",
    )
    await session.commit()

    latest = await snapshots.latest_for_product(product.id)
    assert len(latest) == 1
    assert latest[0].price == Decimal("10.00")


async def test_alert_event_cas_delivered(session: AsyncSession) -> None:
    users = UserRepository(session)
    servers = ServerRepository(session)
    products = ProductRepository(session)
    watches = WatchRepository(session)
    alerts = AlertEventRepository(session)

    user = await users.create(discord_id=10003)
    server = await servers.create(guild_id=20003)
    product = await products.create(source_url="https://example.com/p/4", domain="example.com")
    watch = await watches.create(
        server_id=server.id,
        added_by_user_id=user.id,
        product_id=product.id,
        alert_rules={"drop": True},
    )
    await session.commit()

    event = await alerts.create(
        watch_id=watch.id,
        rule_type="drop",
        previous_price=Decimal("20.00"),
        new_price=Decimal("15.00"),
        previous_in_stock=True,
        new_in_stock=True,
        payload={"reason": "drop"},
    )
    await session.commit()

    assert event.delivery_status == "pending"
    assert await alerts.mark_delivered(event.id) is True
    await session.commit()

    # second attempt is a no-op (CAS)
    assert await alerts.mark_delivered(event.id) is False
