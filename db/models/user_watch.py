from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, uuid_pk

if TYPE_CHECKING:
	from db.models.listing import Listing


class UserWatch(Base):
	__tablename__ = "user_watches"
	__table_args__ = (UniqueConstraint("discord_user_id", "listing_id"),)

	id: Mapped[uuid.UUID] = uuid_pk()
	discord_user_id: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
	listing_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("listings.id"), index=True, nullable=False)
	alert_on_drop: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	alert_on_rise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
	alert_on_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

	listing: Mapped[Listing] = relationship(back_populates="watches")

