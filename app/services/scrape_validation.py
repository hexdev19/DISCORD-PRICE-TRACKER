from __future__ import annotations

from collections.abc import Sequence
from statistics import median
from typing import Literal

from app.config.limits import (
    VALIDATION_ARBITRATE_CONFIDENCE,
    VALIDATION_MAGNITUDE_RATIO,
    VALIDATION_MIN_HISTORY,
    VALIDATION_PENALTY,
    VALIDATION_PRICE_BAND_FACTOR,
    VALIDATION_SUSPECT_CONFIDENCE,
)
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.scraper import validate
from app.scraper.schemas import ScrapeResult

ScrapeDecision = Literal["trust", "suspect", "arbitrate"]

_IDENTITY_FLAGS = ("identifier_drift", "title_drift")


def _recent_prices(snapshots: Sequence[PriceSnapshot]) -> list[float]:
    return [float(s.price) for s in snapshots if s.price is not None]


def _identifier_drift(result: ScrapeResult, product: Product) -> bool:
    for field in ("asin", "gtin", "mpn"):
        stored = getattr(product, field)
        incoming = getattr(result, field)
        if stored and incoming and stored != incoming:
            return True
    return False


def _stock_flapping(snapshots: Sequence[PriceSnapshot]) -> bool:
    priced = [s for s in snapshots if s.price is not None and s.in_stock is not None]
    if len(priced) < VALIDATION_MIN_HISTORY:
        return False
    prices = {s.price for s in priced}
    states = {s.in_stock for s in priced}
    return len(prices) == 1 and len(states) > 1


def stateful_flags(
    result: ScrapeResult,
    product: Product,
    snapshots: Sequence[PriceSnapshot],
) -> list[str]:
    flags: list[str] = []
    prices = _recent_prices(snapshots)

    if result.price is not None and len(prices) >= VALIDATION_MIN_HISTORY:
        med = median(prices)
        new = float(result.price)
        if med > 0:
            if validate.ratio_exceeds(new, med, VALIDATION_MAGNITUDE_RATIO):
                flags.append("magnitude_change")
            if not med / VALIDATION_PRICE_BAND_FACTOR <= new <= med * VALIDATION_PRICE_BAND_FACTOR:
                flags.append("price_out_of_band")

    if result.currency and product.currency and result.currency != product.currency:
        flags.append("currency_flip")

    if _identifier_drift(result, product):
        flags.append("identifier_drift")
    if result.title and product.title and validate.titles_disagree(result.title, product.title):
        flags.append("title_drift")
    if _stock_flapping(snapshots):
        flags.append("stock_flapping")

    return flags


def decide(confidence: float, flags: list[str]) -> ScrapeDecision:
    if confidence < VALIDATION_ARBITRATE_CONFIDENCE or any(f in flags for f in _IDENTITY_FLAGS):
        return "arbitrate"
    if confidence < VALIDATION_SUSPECT_CONFIDENCE:
        return "suspect"
    return "trust"


def validate_snapshot(
    result: ScrapeResult,
    product: Product,
    snapshots: Sequence[PriceSnapshot],
) -> tuple[float, list[str], ScrapeDecision]:
    flags = [*result.flags, *stateful_flags(result, product, snapshots)]
    confidence = min(result.confidence, max(0.0, 1.0 - VALIDATION_PENALTY * len(flags)))
    return confidence, flags, decide(confidence, flags)


__all__ = [
    "ScrapeDecision",
    "decide",
    "stateful_flags",
    "validate_snapshot",
]
