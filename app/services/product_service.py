from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product_repo import ProductRepository
from app.services.errors import InvalidInput
from app.utils.url_utils import UnsafeURLError, canonicalize_url, domain_of


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)

    async def find_or_create_by_url(
        self,
        raw_url: str,
        *,
        region: str | None = None,
    ) -> tuple[Product, bool]:
        try:
            canonical = canonicalize_url(raw_url)
        except UnsafeURLError as exc:
            raise InvalidInput(str(exc)) from exc

        existing = await self.products.get_by_source_url(canonical)
        if existing is not None:
            return existing, False

        domain = domain_of(canonical)
        product = await self.products.create(source_url=canonical, domain=domain, region=region)
        return product, True
