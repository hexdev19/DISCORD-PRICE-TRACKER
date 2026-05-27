from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.limits import WATCHES_PER_SERVER, WATCHES_PER_USER_PER_SERVER
from app.repositories.product_repo import ProductRepository
from app.services import queue
from app.services.errors import AlreadyExists, LimitExceeded, PermissionDenied
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


async def _make_actors(session: AsyncSession, *, guild_id: int, discord_id: int) -> None:
    await UserService(session).upsert_from_discord(discord_id=discord_id)
    await ServerService(session).upsert_from_discord(guild_id=guild_id)
    await session.commit()


async def test_add_watch_happy_path(session: AsyncSession) -> None:
    await _make_actors(session, guild_id=3001, discord_id=4001)
    svc = WatchService(session)
    watch = await svc.add_watch(
        guild_id=3001, discord_user_id=4001, raw_url="https://example.com/p/1"
    )
    await session.commit()
    assert watch.alert_rules == {"drop": True, "restock": True}
    assert len(watch.short_id) == 8


async def test_duplicate_url_in_server_rejected(session: AsyncSession) -> None:
    await _make_actors(session, guild_id=3002, discord_id=4002)
    svc = WatchService(session)
    await svc.add_watch(
        guild_id=3002, discord_user_id=4002, raw_url="https://example.com/p/dup"
    )
    await session.commit()

    with pytest.raises(AlreadyExists):
        await svc.add_watch(
            guild_id=3002, discord_user_id=4002, raw_url="https://example.com/p/dup?utm_source=x"
        )


async def test_per_server_cap_enforced(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(WATCHES_PER_SERVER, "free", 2)
    monkeypatch.setitem(WATCHES_PER_USER_PER_SERVER, "free", 99)

    await _make_actors(session, guild_id=3003, discord_id=4003)
    svc = WatchService(session)
    await svc.add_watch(guild_id=3003, discord_user_id=4003, raw_url="https://e.com/p/a")
    await svc.add_watch(guild_id=3003, discord_user_id=4003, raw_url="https://e.com/p/b")
    await session.commit()

    with pytest.raises(LimitExceeded) as excinfo:
        await svc.add_watch(guild_id=3003, discord_user_id=4003, raw_url="https://e.com/p/c")
    assert excinfo.value.limit_name == "watches_per_server"


async def test_per_user_cap_enforced(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(WATCHES_PER_USER_PER_SERVER, "free", 1)

    await _make_actors(session, guild_id=3004, discord_id=4004)
    svc = WatchService(session)
    await svc.add_watch(guild_id=3004, discord_user_id=4004, raw_url="https://e.com/p/x")
    await session.commit()

    with pytest.raises(LimitExceeded) as excinfo:
        await svc.add_watch(guild_id=3004, discord_user_id=4004, raw_url="https://e.com/p/y")
    assert excinfo.value.limit_name == "watches_per_user_per_server"


async def test_remove_requires_owner_or_admin(session: AsyncSession) -> None:
    await _make_actors(session, guild_id=3005, discord_id=4005)
    await UserService(session).upsert_from_discord(discord_id=4006)
    await session.commit()

    svc = WatchService(session)
    watch = await svc.add_watch(
        guild_id=3005, discord_user_id=4005, raw_url="https://e.com/p/own"
    )
    await session.commit()

    with pytest.raises(PermissionDenied):
        await svc.remove(watch_id=watch.id, discord_user_id=4006, is_admin=False)

    await svc.remove(watch_id=watch.id, discord_user_id=4006, is_admin=True)
    await session.commit()
    assert watch.removed_at is not None


async def test_manual_refresh_enqueues_high_priority(
    session: AsyncSession, _wire_queue: _RecordingQueue
) -> None:
    await _make_actors(session, guild_id=3006, discord_id=4007)
    svc = WatchService(session)
    watch = await svc.add_watch(
        guild_id=3006, discord_user_id=4007, raw_url="https://e.com/p/ref"
    )
    await session.commit()

    await svc.request_refresh(watch_id=watch.id, discord_user_id=4007, is_admin=False)
    assert _wire_queue.calls == [
        ("scrape.product", [str(watch.product_id)], "scrape.adapter"),
    ]


async def test_remove_keeps_product_row(session: AsyncSession) -> None:
    """Soft-delete preserves the products row so other servers share it."""
    await _make_actors(session, guild_id=3007, discord_id=4008)
    svc = WatchService(session)
    watch = await svc.add_watch(
        guild_id=3007, discord_user_id=4008, raw_url="https://e.com/p/keep"
    )
    await session.commit()

    await svc.remove(watch_id=watch.id, discord_user_id=4008, is_admin=False)
    await session.commit()

    product = await ProductRepository(session).get(watch.product_id)
    assert product is not None
