from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import delete, select

from app.config.limits import SOFT_DELETE_GRACE_DAYS
from app.db.session import SessionFactory
from app.models.alert_event import AlertEvent
from app.models.membership import ServerMembership
from app.models.price_snapshot import PriceSnapshot
from app.models.server import Server
from app.models.user import User
from app.models.watch import Watch
from app.repositories.audit_repo import AuditLogRepository
from app.utils.logger import get_logger

log = get_logger(__name__)


async def _cleanup_servers() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SOFT_DELETE_GRACE_DAYS)
    removed = 0
    async with SessionFactory() as session:
        stale = (
            await session.execute(
                select(Server).where(
                    Server.is_active.is_(False),
                    Server.removed_at.isnot(None),
                    Server.removed_at < cutoff,
                )
            )
        ).scalars().all()

        for server in stale:
            watch_ids = list(
                (
                    await session.execute(
                        select(Watch.id).where(Watch.server_id == server.id)
                    )
                ).scalars()
            )
            if watch_ids:
                await session.execute(
                    delete(AlertEvent).where(AlertEvent.watch_id.in_(watch_ids))
                )
                await session.execute(delete(Watch).where(Watch.id.in_(watch_ids)))
            await session.execute(
                delete(ServerMembership).where(ServerMembership.server_id == server.id)
            )
            await AuditLogRepository(session).record(
                action="server.purged",
                actor_type="system",
                target_type="server",
                target_id=str(server.id),
            )
            await session.delete(server)
            removed += 1
        await session.commit()
    log.info("housekeeping.servers_purged", count=removed)
    return removed


async def _cleanup_accounts() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SOFT_DELETE_GRACE_DAYS)
    removed = 0
    async with SessionFactory() as session:
        stale = (
            await session.execute(
                select(User).where(
                    User.deleted_at.isnot(None),
                    User.deleted_at < cutoff,
                )
            )
        ).scalars().all()

        for user in stale:
            await session.execute(
                delete(ServerMembership).where(ServerMembership.user_id == user.id)
            )
            await AuditLogRepository(session).record(
                action="account.purged",
                actor_type="system",
                target_type="user",
                target_id=str(user.id),
            )
            await session.delete(user)
            removed += 1

        orphan_snapshots = await session.execute(
            select(PriceSnapshot.id).where(
                PriceSnapshot.observed_at
                < datetime.now(timezone.utc) - timedelta(days=365)
            )
        )
        orphan_ids = list(orphan_snapshots.scalars())
        if orphan_ids:
            await session.execute(
                delete(PriceSnapshot).where(PriceSnapshot.id.in_(orphan_ids))
            )

        await session.commit()
    log.info("housekeeping.accounts_purged", count=removed)
    return removed


@shared_task(name="maintenance.cleanup_servers")
def cleanup_servers_task() -> int:
    return asyncio.run(_cleanup_servers())


@shared_task(name="maintenance.cleanup_accounts")
def cleanup_accounts_task() -> int:
    return asyncio.run(_cleanup_accounts())
