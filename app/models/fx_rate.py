from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CHAR, BigInteger, Date, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FxRate(Base):
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    base: Mapped[str] = mapped_column(CHAR(3), default="USD", server_default="USD")
    rates: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
