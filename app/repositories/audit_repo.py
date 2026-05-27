from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

ActorType = Literal["user", "system"]


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        action: str,
        actor_type: ActorType,
        actor_id: str | None = None,
        server_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            server_id=server_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            payload=payload or {},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
