from __future__ import annotations

import structlog

BoundLogger = structlog.stdlib.BoundLogger


def get_logger(name: str | None = None) -> BoundLogger:
    return structlog.get_logger(name)
