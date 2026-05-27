from __future__ import annotations

import pytest

from app.bot.responses import format_error
from app.services.errors import (
    AlreadyExists,
    InvalidInput,
    LimitExceeded,
    NotFound,
    PermissionDenied,
    ServiceError,
)


@pytest.mark.parametrize(
    "exc,phrase",
    [
        (LimitExceeded(limit_name="watches_per_server", value=25), "25/25"),
        (LimitExceeded(limit_name="watches_per_user_per_server", value=10), "10 watches here"),
        (AlreadyExists("already tracked as ABC"), "already tracked"),
        (InvalidInput("bad scheme"), "public product URL"),
        (PermissionDenied("nope"), "owner or a server admin"),
        (NotFound("missing"), "Not found"),
        (ServiceError("???"), "Something went wrong"),
    ],
)
def test_format_error_maps_to_user_message(exc: ServiceError, phrase: str) -> None:
    assert phrase in format_error(exc)
