from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
	from db.models.listing_history import ListingHistory
	from db.models.product import Product
	from db.models.store import Store
	from db.models.user_watch import UserWatch


class Listing(Base, TimestampMixin):
	__tablename__ = "listings"

	id: Mapped[uuid.UUID] = uuid_pk()
	product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
	store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), index=True, nullable=False)
	url: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	current_price: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
	currency: Mapped[str] = mapped_column(String(10), nullable=False)
	in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	product: Mapped[Product] = relationship(back_populates="listings")
	store: Mapped[Store] = relationship(back_populates="listings")
	history: Mapped[list[ListingHistory]] = relationship(back_populates="listing")
	watches: Mapped[list[UserWatch]] = relationship(back_populates="listing")

