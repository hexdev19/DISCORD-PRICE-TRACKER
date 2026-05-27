from __future__ import annotations

import asyncio
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from celery import shared_task
from sqlalchemy import delete, select

from app.config.limits import (
    CIRCUIT_OPEN_INITIAL_SECONDS,
    PRICE_HISTORY_DAYS,
)
from app.db.session import SessionFactory
from app.models.fx_rate import FxRate
from app.models.price_snapshot import PriceSnapshot
from app.utils.logger import get_logger
from app.workers.redis import async_client

log = get_logger(__name__)

_FX_ENDPOINT = "https://api.frankfurter.app/latest"


async def _refresh_fx(*, client: httpx.AsyncClient | None = None) -> bool:
    own_client = client is None
    http = client or httpx.AsyncClient(timeout=10.0)
    try:
        response = await http.get(_FX_ENDPOINT, params={"from": "USD"})
    except httpx.RequestError as exc:
        log.warning("fx.fetch_failed", error=type(exc).__name__)
        return False
    finally:
        if own_client:
            await http.aclose()

    if response.status_code != 200:
        log.warning("fx.fetch_bad_status", status=response.status_code)
        return False

    body = response.json()
    rates = body.get("rates")
    if not isinstance(rates, dict):
        return False

    today = date.fromisoformat(body.get("date", date.today().isoformat()))
    async with SessionFactory() as session:
        existing = (
            await session.execute(select(FxRate).where(FxRate.date == today))
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                FxRate(
                    date=today,
                    base=body.get("base", "USD"),
                    rates=rates,
                    fetched_at=datetime.now(timezone.utc),
                )
            )
        else:
            existing.rates = rates
            existing.fetched_at = datetime.now(timezone.utc)
        await session.commit()
    log.info("fx.refreshed", count=len(rates))
    return True


async def _prune_snapshots() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=PRICE_HISTORY_DAYS)
    total = 0
    async with SessionFactory() as session:
        while True:
            ids_stmt = (
                select(PriceSnapshot.id)
                .where(PriceSnapshot.observed_at < cutoff)
                .limit(10_000)
            )
            ids = [row for row in (await session.execute(ids_stmt)).scalars().all()]
            if not ids:
                break
            await session.execute(delete(PriceSnapshot).where(PriceSnapshot.id.in_(ids)))
            await session.commit()
            total += len(ids)
            await asyncio.sleep(0.1)
    log.info("snapshots.pruned", count=total, retention_days=PRICE_HISTORY_DAYS)
    return total


async def _circuit_probe() -> int:
    redis = async_client()
    transitioned = 0
    cursor: Any = 0
    while True:
        cursor, keys = await redis.scan(cursor=cursor, match="circuit:*:opened_at", count=200)
        for key in keys:
            opened_raw = await redis.get(key)
            if opened_raw is None:
                continue
            timeout_key = key.replace(":opened_at", ":timeout")
            timeout_raw = await redis.get(timeout_key)
            timeout = float(timeout_raw or CIRCUIT_OPEN_INITIAL_SECONDS)
            if time.time() - float(opened_raw) < timeout:
                continue
            transitioned += 1
        if cursor in (0, "0"):
            break
    log.info("circuit.probe", half_open=transitioned)
    return transitioned


@shared_task(name="maintenance.refresh_fx")
def refresh_fx_task() -> bool:
    return asyncio.run(_refresh_fx())


@shared_task(name="maintenance.prune_snapshots")
def prune_snapshots_task() -> int:
    return asyncio.run(_prune_snapshots())


@shared_task(name="maintenance.circuit_probe")
def circuit_probe_task() -> int:
    return asyncio.run(_circuit_probe())
