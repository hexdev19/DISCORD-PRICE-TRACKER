from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Store


class StoreRepository:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_by_domain(self, domain: str) -> Store | None:
		stmt = select(Store).where(Store.domain == domain)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_or_create(self, name: str, domain: str, country: str | None) -> Store:
		existing = await self.get_by_domain(domain)
		if existing is not None:
			return existing
		store = Store(name=name, domain=domain, country=country)
		self.session.add(store)
		await self.session.flush()
		return store

