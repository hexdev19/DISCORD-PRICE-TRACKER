from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing, UserWatch


class ListingRepository:
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_by_url(self, url: str) -> Listing | None:
		stmt = select(Listing).where(Listing.url == url)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_by_id(self, listing_id: UUID) -> Listing | None:
		stmt = select(Listing).where(Listing.id == listing_id)
		result = await self.session.execute(stmt)
		return result.scalar_one_or_none()

	async def get_user_listings(self, discord_user_id: str) -> list[Listing]:
		stmt = (
			select(Listing)
			.join(UserWatch, UserWatch.listing_id == Listing.id)
			.where(UserWatch.discord_user_id == discord_user_id)
		)
		result = await self.session.execute(stmt)
		return list(result.scalars().all())

	async def get_product_listings(self, product_id: UUID) -> list[Listing]:
		stmt = select(Listing).where(Listing.product_id == product_id)
		result = await self.session.execute(stmt)
		return list(result.scalars().all())

	async def get_product_listings_scoped(self, product_id: UUID) -> list[Listing]:
		stmt = (
			select(Listing)
			.join(UserWatch, UserWatch.listing_id == Listing.id)
			.where(Listing.product_id == product_id)
			.order_by(Listing.current_price.asc())
		)
		result = await self.session.execute(stmt)
		return list(result.scalars().unique().all())

	async def create(
		self,
		product_id: UUID,
		store_id: UUID,
		url: str,
		title: str,
		price: Decimal,
		currency: str,
		in_stock: bool,
	) -> Listing:
		listing = Listing(
			product_id=product_id,
			store_id=store_id,
			url=url,
			title=title,
			current_price=price,
			currency=currency,
			in_stock=in_stock,
		)
		self.session.add(listing)
		await self.session.flush()
		return listing

	async def update_price(self, listing_id: UUID, price: Decimal, in_stock: bool) -> None:
		stmt = (
			update(Listing)
			.where(Listing.id == listing_id)
			.values(
				current_price=price,
				in_stock=in_stock,
				last_checked=datetime.utcnow(),
			)
		)
		await self.session.execute(stmt)

