from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class ServerMembership(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "server_memberships"
    __table_args__ = (UniqueConstraint("server_id", "user_id"),)

    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    is_admin: Mapped[bool] = mapped_column(default=False, server_default="false")
    has_tracker_role: Mapped[bool] = mapped_column(default=False, server_default="false")
    last_seen_at: Mapped[datetime | None]
