from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.errors import (
    AlreadyExists,
    InvalidInput,
    LimitExceeded,
    NotFound,
    PermissionDenied,
    ServiceError,
)

_STATUS_BY_ERROR: dict[type[ServiceError], int] = {
    NotFound: status.HTTP_404_NOT_FOUND,
    PermissionDenied: status.HTTP_403_FORBIDDEN,
    AlreadyExists: status.HTTP_409_CONFLICT,
    LimitExceeded: status.HTTP_429_TOO_MANY_REQUESTS,
    InvalidInput: status.HTTP_400_BAD_REQUEST,
}


def register_error_handlers(app: FastAPI) -> None:
    async def handle(request: Request, exc: ServiceError) -> JSONResponse:
        code = next(
            (
                status_code
                for error, status_code in _STATUS_BY_ERROR.items()
                if isinstance(exc, error)
            ),
            status.HTTP_400_BAD_REQUEST,
        )
        return JSONResponse(status_code=code, content={"detail": str(exc)})

    app.add_exception_handler(ServiceError, handle)  # type: ignore[arg-type]
