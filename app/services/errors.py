from __future__ import annotations


class ServiceError(Exception):
    """Base for service-layer failures translated to user-visible messages."""


class NotFound(ServiceError):
    pass


class AlreadyExists(ServiceError):
    pass


class PermissionDenied(ServiceError):
    pass


class LimitExceeded(ServiceError):
    def __init__(self, *, limit_name: str, value: int) -> None:
        super().__init__(f"{limit_name} exceeded: {value}")
        self.limit_name = limit_name
        self.value = value


class InvalidInput(ServiceError):
    pass
