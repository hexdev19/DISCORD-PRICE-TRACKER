from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing, UserWatch


class WatchRepository:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_by_user_and_listing(self, discord_user_id: str, listing_id: UUID) -> UserWatch | None:
		stmt = select(UserWatch).where(
			UserWatch.discord_user_id == discord_user_id,
			UserWatch.listing_id == listing_id,
		)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def create(self, discord_user_id: str, listing_id: UUID) -> UserWatch:
		watch = UserWatch(discord_user_id=discord_user_id, listing_id=listing_id)
		self.session.add(watch)
		await self.session.flush()
		return watch

	async def delete(self, discord_user_id: str, listing_id: UUID) -> bool:
		watch = await self.get_by_user_and_listing(discord_user_id=discord_user_id, listing_id=listing_id)
		if watch is None:
			return False
		await self.session.delete(watch)
		await self.session.flush()
		return True

	async def get_for_listing(self, listing_id: UUID) -> list[UserWatch]:
		stmt = select(UserWatch).where(UserWatch.listing_id == listing_id)
		result = await self.session.execute(stmt)
		return list(result.scalars().all())

	async def get_user_watches(self, discord_user_id: str, query: str | None = None) -> list[UserWatch]:
		stmt = (
			select(UserWatch)
			.join(Listing, Listing.id == UserWatch.listing_id)
			.where(UserWatch.discord_user_id == discord_user_id)
			.order_by(Listing.title.asc())
		)
		if query:
			stmt = stmt.where(Listing.title.ilike(f"%{query}%"))
		result = await self.session.execute(stmt)
		return list(result.scalars().all())
