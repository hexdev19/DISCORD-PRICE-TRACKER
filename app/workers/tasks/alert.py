from __future__ import annotations

import asyncio
from typing import Any

from celery import shared_task

from app.db.session import SessionFactory
from app.repositories.alert_repo import AlertEventRepository
from app.repositories.audit_repo import AuditLogRepository
from app.repositories.product_repo import ProductRepository
from app.repositories.server_repo import ServerRepository
from app.repositories.watch_repo import WatchRepository
from app.utils.embed_builder import alert_embed
from app.utils.logger import get_logger
from app.workers.discord_dispatcher import DiscordDispatcher, DispatchOutcome

log = get_logger(__name__)

_MAX_ATTEMPTS = 5


async def _dispatch(
    alert_event_id: int,
    *,
    dispatcher: DiscordDispatcher | None = None,
) -> DispatchOutcome | None:
    dispatcher = dispatcher or DiscordDispatcher()
    async with SessionFactory() as session:
        alerts = AlertEventRepository(session)
        event = await alerts.get(alert_event_id)
        if event is None:
            log.warning("dispatch.unknown_event", alert_event_id=alert_event_id)
            return None
        if event.delivery_status != "pending":
            return None

        watch = await WatchRepository(session).get(event.watch_id)
        if watch is None:
            log.warning("dispatch.watch_gone", alert_event_id=alert_event_id)
            return None

        product = await ProductRepository(session).get(watch.product_id)
        server = await ServerRepository(session).get(watch.server_id)
        if product is None or server is None:
            return None

        channel_id = watch.alert_channel_id or server.default_alert_channel_id
        if channel_id is None:
            await _mark_failed(session, event, "channel_missing")
            await session.commit()
            return DispatchOutcome(status="channel_gone", detail="no channel configured")

        embed = alert_embed(event, watch, product)
        content = f"<@&{watch.alert_role_id or server.default_alert_role_id}>" if (
            watch.alert_role_id or server.default_alert_role_id
        ) else None

        outcome = await dispatcher.send_message(
            channel_id=channel_id, embed=embed, content=content
        )

        if outcome.status == "delivered":
            await alerts.mark_delivered(event.id)
            await session.commit()
            log.info("alert.dispatched", alert_event_id=event.id)
            return outcome

        if outcome.status == "rate_limited":
            await _bump_attempt(session, event, "rate_limited")
            await session.commit()
            return outcome

        if outcome.status in ("permission_denied", "channel_gone"):
            await _mark_failed(session, event, outcome.status, payload=_payload(outcome))
            if watch.alert_channel_id is not None and outcome.status == "channel_gone":
                watch.alert_channel_id = None
            await AuditLogRepository(session).record(
                action="alert.delivery_failed_perm",
                actor_type="system",
                server_id=server.id,
                target_type="alert_event",
                target_id=str(event.id),
                payload={"status": outcome.status},
            )
            await session.commit()
            return outcome

        await _bump_attempt(session, event, outcome.status, payload=_payload(outcome))
        await session.commit()
        return outcome


async def _bump_attempt(
    session: Any,
    event: Any,
    status: str,
    *,
    payload: dict[str, Any] | None = None,
) -> None:
    event.delivery_attempts = (event.delivery_attempts or 0) + 1
    event.last_error = status
    if event.delivery_attempts >= _MAX_ATTEMPTS:
        event.delivery_status = "failed"


async def _mark_failed(
    session: Any,
    event: Any,
    reason: str,
    *,
    payload: dict[str, Any] | None = None,
) -> None:
    event.delivery_status = "failed"
    event.last_error = reason
    event.delivery_attempts = (event.delivery_attempts or 0) + 1


def _payload(outcome: DispatchOutcome) -> dict[str, Any]:
    return {"status": outcome.status, "detail": outcome.detail}


@shared_task(
    name="alert.dispatch",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=7200,
    retry_jitter=True,
    max_retries=_MAX_ATTEMPTS,
)
def dispatch_task(alert_event_id: int) -> None:
    outcome = asyncio.run(_dispatch(alert_event_id))
    if outcome is None:
        return
    if outcome.status == "rate_limited" and outcome.retry_after is not None:
        from celery import current_task

        raise current_task.retry(countdown=outcome.retry_after)  # type: ignore[union-attr]
