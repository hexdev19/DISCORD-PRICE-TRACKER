from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.product_repo import ProductRepository
from app.scraper.schemas import ScrapeResult
from app.services.errors import NotFound
from app.services.price_service import PriceService
from app.services.product_service import ProductService

pytestmark = pytest.mark.integration


async def test_record_snapshot_updates_product_last_fields(
    session: AsyncSession,
) -> None:
    product, _ = await ProductService(session).find_or_create_by_url(
        "https://example.com/p/snap"
    )
    await session.commit()

    svc = PriceService(session)
    result = ScrapeResult(
        status="ok",
        tier_used=1,
        title="Demo",
        image_url="https://example.com/img.jpg",
        brand="Acme",
        price=Decimal("99.95"),
        currency="USD",
        in_stock=True,
        gtin="1234567890123",
        region_hint="US",
    )
    snapshot = await svc.record_snapshot(product.id, result)
    await session.commit()

    refreshed = await ProductRepository(session).get(product.id)
    assert refreshed is not None
    assert refreshed.last_known_price == Decimal("99.95")
    assert refreshed.last_known_in_stock is True
    assert refreshed.last_scrape_status == "ok"
    assert refreshed.scrape_tier == 1
    assert refreshed.title == "Demo"
    assert refreshed.brand == "Acme"
    assert refreshed.gtin == "1234567890123"
    assert refreshed.region == "US"
    assert snapshot.price == Decimal("99.95")


async def test_record_snapshot_failed_writes_history_row_with_nulls(
    session: AsyncSession,
) -> None:
    product, _ = await ProductService(session).find_or_create_by_url(
        "https://example.com/p/fail"
    )
    await session.commit()

    svc = PriceService(session)
    result = ScrapeResult(status="failed", tier_used=3)
    snapshot = await svc.record_snapshot(product.id, result)
    await session.commit()

    assert snapshot.price is None
    assert snapshot.in_stock is None
    assert snapshot.scrape_status == "failed"


async def test_record_snapshot_unknown_product_raises(session: AsyncSession) -> None:
    import uuid

    svc = PriceService(session)
    with pytest.raises(NotFound):
        await svc.record_snapshot(uuid.uuid4(), ScrapeResult(status="ok", tier_used=1))
