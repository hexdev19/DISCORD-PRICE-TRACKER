from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.utils.ids import short_id


class Watch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "watches"
    __table_args__ = (UniqueConstraint("server_id", "product_id"),)

    short_id: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, default=short_id, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id"), index=True, nullable=False
    )
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), index=True, nullable=False
    )

    alert_rules: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    alert_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    alert_role_id: Mapped[int | None] = mapped_column(BigInteger)
    region_override: Mapped[str | None] = mapped_column(CHAR(2))

    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", index=True)
    paused_at: Mapped[datetime | None]
    last_alert_at: Mapped[datetime | None]
    removed_at: Mapped[datetime | None]
