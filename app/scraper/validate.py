from __future__ import annotations

import re

from app.config.limits import (
    VALIDATION_CANDIDATE_RATIO,
    VALIDATION_PENALTY,
    VALIDATION_TITLE_MIN_LENGTH,
)
from app.scraper.normalize import currency_for_region, currency_from_text
from app.scraper.schemas import ScrapeResult

_AMBIGUOUS_RE = re.compile(r"(?<![\d.,])\d{1,3}[.,]\d{3}(?![\d.,])")
_PRICE_SMELLS = ("/mo", "/ea", "%", "off", "shipping")
_BLOCK_TITLES = (
    "just a moment",
    "robot check",
    "access denied",
    "page not found",
    "are you a human",
)


def is_ambiguous_locale(price_text: str | None) -> bool:
    return bool(price_text) and bool(_AMBIGUOUS_RE.search(str(price_text)))


def has_price_smell(price_text: str | None) -> bool:
    if not price_text:
        return False
    lowered = str(price_text).lower()
    return any(smell in lowered for smell in _PRICE_SMELLS)


def currency_conflicts(price_text: str | None, currency: str | None, region: str | None) -> bool:
    if not currency:
        return False
    text_currency = currency_from_text(price_text)
    if text_currency is not None and text_currency != currency:
        return True
    region_currency = currency_for_region(region)
    if text_currency is None and region_currency is not None:
        return region_currency != currency
    return False


def candidates_disagree(candidates: list[float] | None) -> bool:
    if not candidates or len(candidates) < 2:
        return False
    ordered = sorted({c for c in candidates if c > 0}, reverse=True)
    if len(ordered) < 2:
        return False
    return ordered[0] > ordered[1] * VALIDATION_CANDIDATE_RATIO


def is_block_title(title: str | None) -> bool:
    if not title:
        return True
    lowered = title.strip().lower()
    if len(lowered) < VALIDATION_TITLE_MIN_LENGTH:
        return True
    return any(block in lowered for block in _BLOCK_TITLES)


def assess_result(result: ScrapeResult) -> tuple[float, list[str]]:
    flags: list[str] = []
    fp = result.raw_fingerprint
    price_text = fp.get("price_text")

    if is_ambiguous_locale(price_text):
        flags.append("ambiguous_locale")
    if currency_conflicts(price_text, result.currency, result.region_hint):
        flags.append("currency_conflict")
    if has_price_smell(price_text):
        flags.append("price_smell")
    if result.tier_used == 2 and candidates_disagree(fp.get("price_candidates")):
        flags.append("candidate_disagreement")
    if is_block_title(result.title):
        flags.append("block_page_title")
    if result.in_stock is True and result.price is None:
        flags.append("stock_without_price")

    confidence = max(0.0, 1.0 - VALIDATION_PENALTY * len(flags))
    return confidence, flags


__all__ = ["assess_result"]
