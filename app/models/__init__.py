"""ORM model surface.

Importing this package registers every mapper against ``Base.metadata``.
Alembic's env.py imports ``metadata`` from here for autogenerate.
"""

from __future__ import annotations

from app.models.alert_event import AlertEvent
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.fx_rate import FxRate
from app.models.membership import ServerMembership
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.models.server import Server
from app.models.user import User
from app.models.watch import Watch

metadata = Base.metadata

__all__ = [
    "AlertEvent",
    "AuditLog",
    "Base",
    "FxRate",
    "PriceSnapshot",
    "Product",
    "Server",
    "ServerMembership",
    "User",
    "Watch",
    "metadata",
]
