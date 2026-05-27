from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    discord_username: Mapped[str | None] = mapped_column(Text)
    discord_avatar: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)

    oauth_access_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    oauth_refresh_token_enc: Mapped[bytes | None] = mapped_column(LargeBinary)
    oauth_expires_at: Mapped[datetime | None]

    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    plan: Mapped[str] = mapped_column(String(16), default="free", server_default="free")

    deleted_at: Mapped[datetime | None]
