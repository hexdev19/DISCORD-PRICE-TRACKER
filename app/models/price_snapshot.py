from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, BigInteger, ForeignKey, Index, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriceSnapshot(Base):
    """High-volume append-only history. Never UPDATE rows."""

    __tablename__ = "price_snapshots"
    __table_args__ = (
        Index("ix_price_snapshots_product_time", "product_id", "observed_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    observed_at: Mapped[datetime] = mapped_column(nullable=False, index=True)

    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(CHAR(3))
    in_stock: Mapped[bool | None]
    source_tier: Mapped[int | None] = mapped_column(SmallInteger)
    scrape_status: Mapped[str | None] = mapped_column(String(16))
