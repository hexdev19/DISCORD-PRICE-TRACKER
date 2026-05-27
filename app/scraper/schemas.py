from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

ScrapeStatus = Literal["ok", "partial", "failed"]
   
ScrapeErrorCode = Literal[
    "ssrf_blocked",
    "fetch_failed",
    "timeout",
    "blocked",
    "rate_limited",
    "circuit_open",
    "no_extractor",
    "invalid_response",
    "no_price",
]


class ScrapeError(BaseModel):
    code: ScrapeErrorCode
    message: str | None = None


class ScrapeResult(BaseModel):
    status: ScrapeStatus
    tier_used: int

    title: str | None = None
    image_url: str | None = None
    brand: str | None = None

    price: Decimal | None = None
    currency: str | None = None
    in_stock: bool | None = None

    gtin: str | None = None
    mpn: str | None = None
    asin: str | None = None

    region_hint: str | None = None
    raw_fingerprint: dict[str, Any] = Field(default_factory=dict)
    error: ScrapeError | None = None

    @property
    def is_ok(self) -> bool:
        return self.status == "ok"
