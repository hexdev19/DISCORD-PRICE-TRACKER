from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
	from db.models.listing import Listing


class Product(Base, TimestampMixin):
	__tablename__ = "products"

	id: Mapped[uuid.UUID] = uuid_pk()
	canonical_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
	brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
	category: Mapped[str | None] = mapped_column(String(120), nullable=True)
	image_url: Mapped[str | None] = mapped_column(nullable=True)

	listings: Mapped[list[Listing]] = relationship(back_populates="product")

