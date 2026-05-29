from __future__ import annotations

import os
from typing import Final


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


WATCHES_PER_SERVER: Final[dict[str, int]] = {
    "free": _env_int("LIMIT_WATCHES_PER_SERVER_FREE", 25),
}
WATCHES_PER_USER_PER_SERVER: Final[dict[str, int]] = {
    "free": _env_int("LIMIT_WATCHES_PER_USER_PER_SERVER_FREE", 10),
}

CHECK_CADENCE_SECONDS: Final[int] = _env_int("LIMIT_CHECK_CADENCE_SECONDS", 6 * 60 * 60)

COMMANDS_PER_USER_PER_MIN: Final[int] = _env_int("LIMIT_CMD_PER_USER_PER_MIN", 10)
COMMANDS_PER_SERVER_PER_MIN: Final[int] = _env_int("LIMIT_CMD_PER_SERVER_PER_MIN", 60)
TRACK_INTERVAL_SECONDS_PER_USER: Final[int] = _env_int("LIMIT_TRACK_INTERVAL_PER_USER", 10)
REFRESH_INTERVAL_SECONDS_PER_WATCH: Final[int] = _env_int("LIMIT_REFRESH_INTERVAL_PER_WATCH", 60)

DOMAIN_CONCURRENCY: Final[int] = _env_int("LIMIT_DOMAIN_CONCURRENCY", 5)
DOMAIN_REQUESTS_PER_MIN: Final[int] = _env_int("LIMIT_DOMAIN_RPM", 30)

URL_MAX_LENGTH: Final[int] = _env_int("LIMIT_URL_MAX_LENGTH", 2048)

PRICE_HISTORY_DAYS: Final[int] = _env_int("LIMIT_PRICE_HISTORY_DAYS", 90)
SOFT_DELETE_GRACE_DAYS: Final[int] = _env_int("LIMIT_SOFT_DELETE_GRACE_DAYS", 30)

SCRAPE_LOCK_TTL_SECONDS: Final[int] = _env_int("LIMIT_SCRAPE_LOCK_TTL", 90)
TIER1_SYNC_BUDGET_SECONDS: Final[int] = _env_int("LIMIT_TIER1_SYNC_BUDGET", 5)
BROWSER_MAX_PAGES: Final[int] = _env_int("LIMIT_BROWSER_MAX_PAGES", 2)
BROWSER_NAV_TIMEOUT_SECONDS: Final[int] = _env_int("LIMIT_BROWSER_NAV_TIMEOUT", 30)
RESPONSE_SIZE_CAP_BYTES: Final[int] = _env_int("LIMIT_RESPONSE_SIZE_CAP", 5 * 1024 * 1024)

CIRCUIT_FAIL_THRESHOLD: Final[int] = _env_int("LIMIT_CIRCUIT_FAIL_THRESHOLD", 3)
CIRCUIT_OPEN_INITIAL_SECONDS: Final[int] = _env_int("LIMIT_CIRCUIT_OPEN_INITIAL", 15 * 60)
CIRCUIT_OPEN_MAX_SECONDS: Final[int] = _env_int("LIMIT_CIRCUIT_OPEN_MAX", 6 * 60 * 60)

COOLDOWN_DROP_SECONDS: Final[int] = _env_int("LIMIT_COOLDOWN_DROP", 60 * 60)
COOLDOWN_THRESHOLD_SECONDS: Final[int] = _env_int("LIMIT_COOLDOWN_THRESHOLD", 24 * 60 * 60)
COOLDOWN_RESTOCK_SECONDS: Final[int] = _env_int("LIMIT_COOLDOWN_RESTOCK", 60 * 60)

PRICE_MIN: Final[str] = "0.01"
PRICE_MAX: Final[str] = "1000000.00"

VALIDATION_TITLE_MIN_LENGTH: Final[int] = _env_int("LIMIT_VALIDATION_TITLE_MIN_LENGTH", 3)
VALIDATION_CANDIDATE_RATIO: Final[float] = _env_float("LIMIT_VALIDATION_CANDIDATE_RATIO", 2.0)
VALIDATION_PENALTY: Final[float] = _env_float("LIMIT_VALIDATION_PENALTY", 0.25)

API_REQUESTS_PER_USER_PER_MIN: Final[int] = _env_int("LIMIT_API_REQ_PER_USER", 60)
API_REQUESTS_PER_IP_PER_MIN: Final[int] = _env_int("LIMIT_API_REQ_PER_IP", 300)

MEMBERSHIP_CACHE_TTL_SECONDS: Final[int] = _env_int("LIMIT_MEMBERSHIP_TTL", 5 * 60)
