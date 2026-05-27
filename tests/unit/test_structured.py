from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.scraper.structured import extract_structured

FIXTURES = Path(__file__).parent.parent / "fixtures" / "structured"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_jsonld_extracts_full_product() -> None:
    result = extract_structured(_load("jsonld_full.html"))
    assert result.status == "ok"
    assert result.tier_used == 1
    assert result.title == "Demo Widget"
    assert result.brand == "Acme"
    assert result.price == Decimal("29.99")
    assert result.currency == "EUR"
    assert result.in_stock is True
    assert result.gtin == "1234567890123"
    assert result.mpn == "ACME-001"
    assert result.raw_fingerprint["matched"] == "json-ld"


def test_microdata_fallback_when_no_jsonld() -> None:
    result = extract_structured(_load("microdata.html"))
    assert result.tier_used == 1
    assert result.title == "Microdata Phone"
    assert result.price == Decimal("599.00")
    assert result.currency == "USD"
    assert result.in_stock is False
    assert result.raw_fingerprint["matched"] == "microdata"


def test_opengraph_fallback() -> None:
    result = extract_structured(_load("opengraph_only.html"))
    assert result.tier_used == 1
    assert result.title == "Open Graph Demo"
    assert result.price == Decimal("19.95")
    assert result.currency == "USD"
    assert result.in_stock is True
    assert result.raw_fingerprint["matched"] == "opengraph"


@pytest.mark.parametrize("body", ["", "<html></html>", "not html at all"])
def test_returns_failed_when_no_signals(body: str) -> None:
    result = extract_structured(body)
    assert result.status == "failed"
    assert result.tier_used == 1
