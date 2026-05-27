from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CHAR, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Product(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "products"

    source_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(CHAR(2))

    title: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)

    gtin: Mapped[str | None] = mapped_column(Text)
    mpn: Mapped[str | None] = mapped_column(Text)
    asin: Mapped[str | None] = mapped_column(Text)

    currency: Mapped[str | None] = mapped_column(CHAR(3))
    last_known_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    last_known_in_stock: Mapped[bool | None]
    last_scraped_at: Mapped[datetime | None] = mapped_column(index=True)
    last_scrape_status: Mapped[str | None] = mapped_column(String(16))
    scrape_tier: Mapped[int | None] = mapped_column(SmallInteger)

    circuit_state: Mapped[str] = mapped_column(
        String(16), default="closed", server_default="closed"
    )
