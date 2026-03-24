from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Product


class ProductRepository:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_by_id(self, product_id: UUID) -> Product | None:
		stmt = select(Product).where(Product.id == product_id)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def search_by_name(self, query: str, limit: int = 25) -> list[Product]:
		stmt = (
			select(Product)
			.where(Product.canonical_name.ilike(f"%{query}%"))
			.order_by(Product.canonical_name.asc())
			.limit(limit)
		)
		result = await self.session.execute(stmt)
		return list(result.scalars().all())

	async def find_similar(self, canonical_name: str, threshold: float = 0.85) -> Product | None:
		similarity_score = func.similarity(Product.canonical_name, canonical_name)
		stmt = (
			select(Product)
			.where(similarity_score >= threshold)
			.order_by(similarity_score.desc())
			.limit(1)
		)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def create(self, canonical_name: str, **kwargs: object) -> Product:
		product = Product(canonical_name=canonical_name, **kwargs)
		self.session.add(product)
		await self.session.flush()
		return product

