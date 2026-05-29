from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from app.scraper.schemas import ScrapeResult
from app.scraper.validate import (
    assess_result,
    candidates_disagree,
    currency_conflicts,
    has_price_smell,
    is_ambiguous_locale,
    is_block_title,
)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1.234", True),
        ("1,234", True),
        ("1.23", False),
        ("1.2345", False),
        (None, False),
        ("", False),
    ],
)
def test_is_ambiguous_locale(text: str | None, expected: bool) -> None:
    assert is_ambiguous_locale(text) is expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("$9/mo", True),
        ("$9 /ea", True),
        ("20% off", True),
        ("free shipping", True),
        ("$9.99", False),
        (None, False),
    ],
)
def test_has_price_smell(text: str | None, expected: bool) -> None:
    assert has_price_smell(text) is expected


@pytest.mark.parametrize(
    "text,currency,region,expected",
    [
        ("€9,99", "USD", None, True),
        ("$9.99", "USD", None, False),
        (None, "USD", "DE", True),
        (None, "EUR", "DE", False),
        (None, "USD", None, False),
        ("$9.99", None, None, False),
    ],
)
def test_currency_conflicts(
    text: str | None, currency: str | None, region: str | None, expected: bool
) -> None:
    assert currency_conflicts(text, currency, region) is expected


@pytest.mark.parametrize(
    "candidates,expected",
    [
        ([100.0, 10.0], True),
        ([100.0, 90.0], False),
        ([100.0], False),
        (None, False),
        ([], False),
        ([100.0, 100.0], False),
    ],
)
def test_candidates_disagree(candidates: list[float] | None, expected: bool) -> None:
    assert candidates_disagree(candidates) is expected


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Just a moment...", True),
        ("Robot Check", True),
        ("Access Denied", True),
        ("Page Not Found", True),
        ("Are you a human?", True),
        ("", True),
        (None, True),
        ("ab", True),
        ("Sony WH-1000XM5", False),
    ],
)
def test_is_block_title(title: str | None, expected: bool) -> None:
    assert is_block_title(title) is expected


def _result(**kwargs: Any) -> ScrapeResult:
    base: dict[str, Any] = {
        "status": "ok",
        "tier_used": 1,
        "title": "Good Product",
        "price": Decimal("9.99"),
        "currency": "USD",
        "in_stock": True,
    }
    base.update(kwargs)
    return ScrapeResult(**base)


def test_assess_clean_result_full_confidence() -> None:
    confidence, flags = assess_result(_result())
    assert confidence == 1.0
    assert flags == []


def test_assess_collects_multiple_flags_and_lowers_confidence() -> None:
    result = _result(
        title="Just a moment",
        currency="USD",
        raw_fingerprint={"price_text": "€1.234"},
    )
    confidence, flags = assess_result(result)
    assert "ambiguous_locale" in flags
    assert "currency_conflict" in flags
    assert "block_page_title" in flags
    assert confidence < 1.0


def test_assess_price_smell_flag() -> None:
    _, flags = assess_result(_result(raw_fingerprint={"price_text": "$9.99/mo"}))
    assert flags == ["price_smell"]


def test_assess_stock_without_price() -> None:
    _, flags = assess_result(_result(price=None, currency=None, in_stock=True))
    assert "stock_without_price" in flags


def test_assess_candidate_disagreement_only_tier2() -> None:
    fp = {"price_candidates": [100.0, 10.0]}
    _, tier2_flags = assess_result(_result(tier_used=2, raw_fingerprint=fp))
    assert "candidate_disagreement" in tier2_flags
    _, tier1_flags = assess_result(_result(tier_used=1, raw_fingerprint=fp))
    assert "candidate_disagreement" not in tier1_flags


def test_assess_handles_missing_fingerprint_data() -> None:
    confidence, flags = assess_result(_result(raw_fingerprint={}))
    assert confidence == 1.0
    assert flags == []
