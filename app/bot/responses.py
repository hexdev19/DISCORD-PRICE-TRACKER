from __future__ import annotations

from app.services.errors import (
    AlreadyExists,
    InvalidInput,
    LimitExceeded,
    NotFound,
    PermissionDenied,
    ServiceError,
)

_LIMIT_MESSAGES = {
    "watches_per_server": "This server is at {value}/{value} watches. Use `/untrack` to free a slot.",
    "watches_per_user_per_server": (
        "You've added {value} watches here (your limit). "
        "Have an admin help, or remove one yours first."
    ),
}


def format_error(exc: ServiceError) -> str:
    if isinstance(exc, LimitExceeded):
        template = _LIMIT_MESSAGES.get(
            exc.limit_name, "Limit reached: {limit_name} ({value})."
        )
        return template.format(limit_name=exc.limit_name, value=exc.value)
    if isinstance(exc, AlreadyExists):
        return str(exc) or "Already tracked here."
    if isinstance(exc, InvalidInput):
        return "That URL doesn't look like a public product URL."
    if isinstance(exc, PermissionDenied):
        return "Only the watch owner or a server admin can do this."
    if isinstance(exc, NotFound):
        return "Not found. Use `/list` to see what's tracked here."
    return "Something went wrong. Try again, or run `/help`."
