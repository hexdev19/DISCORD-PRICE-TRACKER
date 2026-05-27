from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.limits import (
    COOLDOWN_DROP_SECONDS,
    COOLDOWN_RESTOCK_SECONDS,
    COOLDOWN_THRESHOLD_SECONDS,
)
from app.models.alert_event import AlertEvent
from app.models.price_snapshot import PriceSnapshot
from app.models.watch import Watch
from app.repositories.alert_repo import AlertEventRepository
from app.repositories.price_repo import PriceSnapshotRepository
from app.repositories.watch_repo import WatchRepository
from app.services import queue
from app.services.cooldown import CooldownStore, InMemoryCooldownStore

_RULE_TYPES = ("drop", "threshold", "restock")
_COOLDOWNS = {
    "drop": COOLDOWN_DROP_SECONDS,
    "threshold": COOLDOWN_THRESHOLD_SECONDS,
    "restock": COOLDOWN_RESTOCK_SECONDS,
}


class AlertService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        cooldowns: CooldownStore | None = None,
    ) -> None:
        self.session = session
        self.watches = WatchRepository(session)
        self.snapshots = PriceSnapshotRepository(session)
        self.alerts = AlertEventRepository(session)
        self._cooldowns: CooldownStore = cooldowns or InMemoryCooldownStore()

    async def evaluate(
        self,
        product_id: uuid.UUID,
        new_snapshot: PriceSnapshot,
    ) -> list[AlertEvent]:
        prev = await self._previous_snapshot(product_id, new_snapshot.id)
        watches = await self.watches.list_active_for_product(product_id)
        events: list[AlertEvent] = []

        for watch in watches:
            for rule in _RULE_TYPES:
                if not _rule_enabled(watch, rule):
                    continue
                if not _rule_fires(rule, watch, prev, new_snapshot):
                    continue

                cooldown_key = f"alert:cooldown:{watch.id}:{rule}"
                if await self._cooldowns.is_cooling(cooldown_key):
                    continue

                event = await self.alerts.create(
                    watch_id=watch.id,
                    rule_type=rule,
                    previous_price=prev.price if prev else None,
                    new_price=new_snapshot.price,
                    previous_in_stock=prev.in_stock if prev else None,
                    new_in_stock=new_snapshot.in_stock,
                    payload=_payload(rule, watch, prev, new_snapshot),
                )
                await self._cooldowns.set_cooldown(cooldown_key, _COOLDOWNS[rule])
                watch.last_alert_at = new_snapshot.observed_at
                events.append(event)
                queue.enqueue_alert_dispatch(event.id)

        return events

    async def _previous_snapshot(
        self, product_id: uuid.UUID, exclude_id: int
    ) -> PriceSnapshot | None:
        rows = await self.snapshots.latest_for_product(product_id, limit=2)
        for row in rows:
            if row.id != exclude_id:
                return row
        return None


def _rule_enabled(watch: Watch, rule: str) -> bool:
    rules = watch.alert_rules or {}
    if rule == "threshold":
        return rules.get("threshold") not in (None, False)
    return bool(rules.get(rule))


def _rule_fires(
    rule: str,
    watch: Watch,
    prev: PriceSnapshot | None,
    new: PriceSnapshot,
) -> bool:
    if rule == "drop":
        if prev is None or prev.price is None or new.price is None:
            return False
        if new.in_stock is False:
            return False
        return new.price < prev.price

    if rule == "threshold":
        if new.price is None:
            return False
        threshold_raw = (watch.alert_rules or {}).get("threshold")
        if threshold_raw is None:
            return False
        try:
            threshold = Decimal(str(threshold_raw))
        except (ValueError, ArithmeticError):
            return False
        return new.price <= threshold

    if rule == "restock":
        return prev is not None and prev.in_stock is False and new.in_stock is True

    return False


def _payload(
    rule: str,
    watch: Watch,
    prev: PriceSnapshot | None,
    new: PriceSnapshot,
) -> dict[str, Any]:
    return {
        "rule": rule,
        "watch_short_id": watch.short_id,
        "previous_price": str(prev.price) if prev and prev.price is not None else None,
        "new_price": str(new.price) if new.price is not None else None,
        "currency": new.currency,
        "previous_in_stock": prev.in_stock if prev else None,
        "new_in_stock": new.in_stock,
    }
