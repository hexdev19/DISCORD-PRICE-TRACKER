from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_snapshot import PriceSnapshot
from app.repositories.price_repo import PriceSnapshotRepository
from app.repositories.product_repo import ProductRepository
from app.scraper.schemas import ScrapeResult
from app.services.errors import NotFound


class PriceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.snapshots = PriceSnapshotRepository(session)

    async def record_snapshot(
        self,
        product_id: uuid.UUID,
        result: ScrapeResult,
    ) -> PriceSnapshot:
        product = await self.products.get(product_id)
        if product is None:
            raise NotFound("product not found")

        observed_at = datetime.now(timezone.utc)
        status = result.status
        tier = result.tier_used or 0

        snapshot = await self.snapshots.append(
            product_id=product.id,
            observed_at=observed_at,
            price=result.price,
            currency=result.currency,
            in_stock=result.in_stock,
            source_tier=tier,
            scrape_status=status,
        )

        await self.products.update_last_scrape(
            product,
            observed_at=observed_at,
            price=result.price,
            currency=result.currency,
            in_stock=result.in_stock,
            status=status,
            tier=tier,
        )

        if result.title and not product.title:
            product.title = result.title
        if result.image_url and not product.image_url:
            product.image_url = result.image_url
        if result.brand and not product.brand:
            product.brand = result.brand
        if result.gtin and not product.gtin:
            product.gtin = result.gtin
        if result.mpn and not product.mpn:
            product.mpn = result.mpn
        if result.asin and not product.asin:
            product.asin = result.asin
        if result.region_hint and not product.region:
            product.region = result.region_hint

        return snapshot

    async def latest(self, product_id: uuid.UUID) -> PriceSnapshot | None:
        rows = await self.snapshots.latest_for_product(product_id, limit=1)
        return rows[0] if rows else None
