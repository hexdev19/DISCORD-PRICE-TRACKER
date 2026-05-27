from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

_SENSITIVE_EXACT = frozenset(
    {"authorization", "cookie", "set-cookie", "password", "secret", "session"}
)
_SENSITIVE_SUBSTR = ("token", "oauth", "api_key", "apikey")
_REDACTED = "[redacted]"
_MAX_STR = 1024
_MAX_LIST = 100


def _redact_sensitive(_: Any, __: str, event_dict: EventDict) -> EventDict:
    for key in list(event_dict.keys()):
        lk = key.lower()
        if lk in _SENSITIVE_EXACT or any(s in lk for s in _SENSITIVE_SUBSTR):
            event_dict[key] = _REDACTED
    return event_dict


def _truncate(_: Any, __: str, event_dict: EventDict) -> EventDict:
    for k, v in event_dict.items():
        if isinstance(v, str) and len(v) > _MAX_STR:
            event_dict[k] = v[:_MAX_STR] + "…"
        elif isinstance(v, list) and len(v) > _MAX_LIST:
            event_dict[k] = v[:_MAX_LIST] + ["…(truncated)"]
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _redact_sensitive,
        _truncate,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
