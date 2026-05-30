from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, db_session
from app.models.alert_event import AlertEvent
from app.models.price_snapshot import PriceSnapshot
from app.models.user import User
from app.services.dashboard_service import (
    DashboardService,
    ServerSummary,
    SnapshotRange,
    WatchDetail,
)

router = APIRouter(tags=["dashboard"])


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class ServerOut(_Model):
    guild_id: str = Field(alias="guildId")
    name: str | None
    icon_hash: str | None = Field(alias="iconHash")
    is_admin: bool = Field(alias="isAdmin")
    watch_count: int = Field(alias="watchCount")


class ServerDetailOut(ServerOut):
    region_default: str | None = Field(alias="regionDefault")


class WatchRowOut(_Model):
    id: str
    short_id: str = Field(alias="shortId")
    title: str | None
    image_url: str | None = Field(alias="imageUrl")
    domain: str
    source_url: str = Field(alias="sourceUrl")
    currency: str | None
    last_price: float | None = Field(alias="lastPrice")
    in_stock: bool | None = Field(alias="inStock")
    is_active: bool = Field(alias="isActive")
    paused: bool
    last_scraped_at: datetime | None = Field(alias="lastScrapedAt")
    alert_rules: dict[str, object] = Field(alias="alertRules")


class ProductOut(_Model):
    title: str | None
    image_url: str | None = Field(alias="imageUrl")
    domain: str
    source_url: str = Field(alias="sourceUrl")
    brand: str | None
    currency: str | None
    last_price: float | None = Field(alias="lastPrice")
    in_stock: bool | None = Field(alias="inStock")
    last_scraped_at: datetime | None = Field(alias="lastScrapedAt")
    last_scrape_status: str | None = Field(alias="lastScrapeStatus")


class AlertOut(_Model):
    id: int
    rule_type: str = Field(alias="ruleType")
    triggered_at: datetime = Field(alias="triggeredAt")
    previous_price: float | None = Field(alias="previousPrice")
    new_price: float | None = Field(alias="newPrice")
    previous_in_stock: bool | None = Field(alias="previousInStock")
    new_in_stock: bool | None = Field(alias="newInStock")
    delivery_status: str = Field(alias="deliveryStatus")


class WatchDetailOut(_Model):
    id: str
    short_id: str = Field(alias="shortId")
    guild_id: str = Field(alias="guildId")
    product: ProductOut
    alert_rules: dict[str, object] = Field(alias="alertRules")
    is_active: bool = Field(alias="isActive")
    paused: bool
    created_at: datetime = Field(alias="createdAt")
    alerts: list[AlertOut]


class SnapshotPointOut(_Model):
    t: datetime
    price: float | None
    in_stock: bool | None = Field(alias="inStock")


class SnapshotsOut(_Model):
    currency: str | None
    points: list[SnapshotPointOut]


def _money(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _server_out(summary: ServerSummary) -> ServerOut:
    return ServerOut(
        guildId=str(summary.server.guild_id),
        name=summary.server.name,
        iconHash=summary.server.icon_hash,
        isAdmin=summary.is_admin,
        watchCount=summary.watch_count,
    )


def _alert_out(alert: AlertEvent) -> AlertOut:
    return AlertOut(
        id=alert.id,
        ruleType=alert.rule_type,
        triggeredAt=alert.triggered_at,
        previousPrice=_money(alert.previous_price),
        newPrice=_money(alert.new_price),
        previousInStock=alert.previous_in_stock,
        newInStock=alert.new_in_stock,
        deliveryStatus=alert.delivery_status,
    )


def _point_out(snapshot: PriceSnapshot) -> SnapshotPointOut:
    return SnapshotPointOut(
        t=snapshot.observed_at, price=_money(snapshot.price), inStock=snapshot.in_stock
    )


@router.get("/servers", response_model=list[ServerOut], response_model_by_alias=True)
async def list_servers(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> list[ServerOut]:
    summaries = await DashboardService(session).list_servers(user)
    return [_server_out(s) for s in summaries]


@router.get("/servers/{guild_id}", response_model=ServerDetailOut, response_model_by_alias=True)
async def get_server(
    guild_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> ServerDetailOut:
    summary = await DashboardService(session).get_server(user, guild_id)
    return ServerDetailOut(
        guildId=str(summary.server.guild_id),
        name=summary.server.name,
        iconHash=summary.server.icon_hash,
        isAdmin=summary.is_admin,
        watchCount=summary.watch_count,
        regionDefault=summary.server.region_default,
    )


@router.get(
    "/servers/{guild_id}/watches",
    response_model=list[WatchRowOut],
    response_model_by_alias=True,
)
async def list_watches(
    guild_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> list[WatchRowOut]:
    rows = await DashboardService(session).list_watches(user, guild_id)
    return [
        WatchRowOut(
            id=str(watch.id),
            shortId=watch.short_id,
            title=product.title,
            imageUrl=product.image_url,
            domain=product.domain,
            sourceUrl=product.source_url,
            currency=product.currency,
            lastPrice=_money(product.last_known_price),
            inStock=product.last_known_in_stock,
            isActive=watch.is_active,
            paused=watch.paused_at is not None,
            lastScrapedAt=product.last_scraped_at,
            alertRules=watch.alert_rules,
        )
        for watch, product in rows
    ]


@router.get("/watches/{watch_id}", response_model=WatchDetailOut, response_model_by_alias=True)
async def get_watch(
    watch_id: uuid.UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> WatchDetailOut:
    detail: WatchDetail = await DashboardService(session).get_watch(user, watch_id)
    return WatchDetailOut(
        id=str(detail.watch.id),
        shortId=detail.watch.short_id,
        guildId=str(detail.server.guild_id),
        product=ProductOut(
            title=detail.product.title,
            imageUrl=detail.product.image_url,
            domain=detail.product.domain,
            sourceUrl=detail.product.source_url,
            brand=detail.product.brand,
            currency=detail.product.currency,
            lastPrice=_money(detail.product.last_known_price),
            inStock=detail.product.last_known_in_stock,
            lastScrapedAt=detail.product.last_scraped_at,
            lastScrapeStatus=detail.product.last_scrape_status,
        ),
        alertRules=detail.watch.alert_rules,
        isActive=detail.watch.is_active,
        paused=detail.watch.paused_at is not None,
        createdAt=detail.watch.created_at,
        alerts=[_alert_out(a) for a in detail.alerts],
    )


@router.get(
    "/watches/{watch_id}/snapshots",
    response_model=SnapshotsOut,
    response_model_by_alias=True,
)
async def get_snapshots(
    watch_id: uuid.UUID,
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> SnapshotsOut:
    until = to or datetime.now(UTC)
    since = from_ or until - timedelta(days=30)
    result: SnapshotRange = await DashboardService(session).get_snapshots(
        user, watch_id, since=since, until=until
    )
    return SnapshotsOut(currency=result.currency, points=[_point_out(p) for p in result.points])
