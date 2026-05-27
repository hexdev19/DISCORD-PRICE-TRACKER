from __future__ import annotations

from datetime import datetime

from sqlalchemy import CHAR, BigInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Server(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "servers"

    guild_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    icon_hash: Mapped[str | None] = mapped_column(Text)

    tracker_role_id: Mapped[int | None] = mapped_column(BigInteger)
    default_alert_channel_id: Mapped[int | None] = mapped_column(BigInteger)
    default_alert_role_id: Mapped[int | None] = mapped_column(BigInteger)
    region_default: Mapped[str | None] = mapped_column(CHAR(2))

    plan: Mapped[str] = mapped_column(String(16), default="free", server_default="free")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())
    removed_at: Mapped[datetime | None]
