from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, uuid_pk

if TYPE_CHECKING:
	from db.models.listing import Listing


class Store(Base):
	__tablename__ = "stores"

	id: Mapped[uuid.UUID] = uuid_pk()
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	domain: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	country: Mapped[str | None] = mapped_column(String(10), nullable=True)
	created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

	listings: Mapped[list[Listing]] = relationship(back_populates="store")
