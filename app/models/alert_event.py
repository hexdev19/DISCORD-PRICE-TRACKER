from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        Index("ix_alert_events_watch_time", "watch_id", "triggered_at"),
        Index(
            "ix_alert_events_pending",
            "id",
            postgresql_where=Text("delivery_status = 'pending'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    watch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("watches.id"), nullable=False
    )
    rule_type: Mapped[str] = mapped_column(String(16), nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    previous_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    new_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    previous_in_stock: Mapped[bool | None]
    new_in_stock: Mapped[bool | None]

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    delivery_status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending", nullable=False
    )
    delivery_attempts: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    delivered_at: Mapped[datetime | None]
    last_error: Mapped[str | None] = mapped_column(Text)
