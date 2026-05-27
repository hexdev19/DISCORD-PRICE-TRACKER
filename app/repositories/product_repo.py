from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, product_id: uuid.UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def get_by_source_url(self, source_url: str) -> Product | None:
        stmt = select(Product).where(Product.source_url == source_url)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, *, source_url: str, domain: str, region: str | None = None) -> Product:
        product = Product(source_url=source_url, domain=domain, region=region)
        self.session.add(product)
        await self.session.flush()
        return product

    async def update_last_scrape(
        self,
        product: Product,
        *,
        observed_at: datetime,
        price: Decimal | None,
        currency: str | None,
        in_stock: bool | None,
        status: str,
        tier: int,
    ) -> None:
        product.last_scraped_at = observed_at
        product.last_known_price = price
        product.currency = currency
        product.last_known_in_stock = in_stock
        product.last_scrape_status = status
        product.scrape_tier = tier
