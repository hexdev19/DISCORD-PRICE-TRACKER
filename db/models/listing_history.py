from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, uuid_pk

if TYPE_CHECKING:
	from db.models.listing import Listing


class ListingHistory(Base):
	__tablename__ = "listing_history"
	__table_args__ = (
		CheckConstraint(
			"change_type IN ('price_drop', 'price_rise', 'restock', 'out_of_stock', 'no_change')",
			name="ck_listing_history_change_type",
		),
	)

	id: Mapped[uuid.UUID] = uuid_pk()
	listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), index=True, nullable=False)
	price: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
	currency: Mapped[str] = mapped_column(String(10), nullable=False)
	in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False)
	price_delta: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
	delta_pct: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
	change_type: Mapped[str] = mapped_column(String(20), nullable=False)
	recorded_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, nullable=False)

	listing: Mapped[Listing] = relationship(back_populates="history")

