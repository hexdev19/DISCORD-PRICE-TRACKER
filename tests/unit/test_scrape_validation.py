from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.scraper.schemas import ScrapeResult
from app.services.scrape_validation import (
    decide,
    stateful_flags,
    validate_snapshot,
)


def _product(**kwargs: Any) -> Product:
    base: dict[str, Any] = {
        "source_url": "https://example.com/p",
        "domain": "example.com",
        "currency": "USD",
        "title": "Sony WH-1000XM5",
    }
    base.update(kwargs)
    return Product(**base)


def _result(**kwargs: Any) -> ScrapeResult:
    base: dict[str, Any] = {
        "status": "ok",
        "tier_used": 1,
        "title": "Sony WH-1000XM5",
        "price": Decimal("100.00"),
        "currency": "USD",
        "in_stock": True,
    }
    base.update(kwargs)
    return ScrapeResult(**base)


def _snapshots(
    prices: list[Decimal | None], stocks: list[bool | None] | None = None
) -> list[PriceSnapshot]:
    pid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    rows: list[PriceSnapshot] = []
    for i, price in enumerate(prices):
        stock = stocks[i] if stocks is not None else True
        rows.append(
            PriceSnapshot(
                product_id=pid,
                observed_at=now - timedelta(hours=i),
                price=price,
                currency="USD",
                in_stock=stock,
                source_tier=1,
                scrape_status="ok",
            )
        )
    return rows


def test_no_history_brand_new_product_has_no_stateful_flags() -> None:
    assert stateful_flags(_result(), _product(), []) == []


def test_price_within_band_no_flag() -> None:
    snaps = _snapshots([Decimal("100"), Decimal("110"), Decimal("90")])
    assert stateful_flags(_result(price=Decimal("120")), _product(), snaps) == []


def test_price_out_of_band_flagged() -> None:
    snaps = _snapshots([Decimal("100"), Decimal("100"), Decimal("100")])
    flags = stateful_flags(_result(price=Decimal("400")), _product(), snaps)
    assert "price_out_of_band" in flags


def test_magnitude_change_flagged() -> None:
    snaps = _snapshots([Decimal("100"), Decimal("100"), Decimal("100")])
    flags = stateful_flags(_result(price=Decimal("100000")), _product(), snaps)
    assert "magnitude_change" in flags
    assert "price_out_of_band" in flags


def test_currency_flip_flagged() -> None:
    flags = stateful_flags(_result(currency="EUR"), _product(currency="USD"), [])
    assert flags == ["currency_flip"]


def test_identifier_drift_flagged() -> None:
    result = _result(asin="NEWASIN")
    flags = stateful_flags(result, _product(asin="OLDASIN"), [])
    assert flags == ["identifier_drift"]


def test_identifier_match_no_flag() -> None:
    result = _result(asin="SAME")
    assert stateful_flags(result, _product(asin="SAME"), []) == []


def test_title_drift_flagged() -> None:
    result = _result(title="Apple AirPods Pro")
    flags = stateful_flags(result, _product(title="Sony WH-1000XM5"), [])
    assert "title_drift" in flags


def test_stock_flapping_flagged() -> None:
    snaps = _snapshots(
        [Decimal("100"), Decimal("100"), Decimal("100")],
        stocks=[True, False, True],
    )
    flags = stateful_flags(_result(price=Decimal("100")), _product(), snaps)
    assert "stock_flapping" in flags


def test_stock_not_flapping_when_price_changes() -> None:
    snaps = _snapshots(
        [Decimal("100"), Decimal("90"), Decimal("80")],
        stocks=[True, False, True],
    )
    flags = stateful_flags(_result(price=Decimal("100")), _product(), snaps)
    assert "stock_flapping" not in flags


@pytest.mark.parametrize(
    "confidence,flags,expected",
    [
        (1.0, [], "trust"),
        (0.8, ["price_smell"], "trust"),
        (0.5, [], "suspect"),
        (0.2, [], "arbitrate"),
        (1.0, ["identifier_drift"], "arbitrate"),
        (0.9, ["title_drift"], "arbitrate"),
    ],
)
def test_decide_tiers(confidence: float, flags: list[str], expected: str) -> None:
    assert decide(confidence, flags) == expected


def test_validate_snapshot_combines_scraper_and_stateful() -> None:
    result = _result(confidence=0.75, flags=["price_smell"], currency="EUR")
    confidence, flags, decision = validate_snapshot(result, _product(currency="USD"), [])
    assert "price_smell" in flags
    assert "currency_flip" in flags
    assert confidence < 0.75
    assert decision in ("trust", "suspect", "arbitrate")


def test_validate_snapshot_identity_drift_forces_arbitrate() -> None:
    result = _result(asin="NEW")
    _, _, decision = validate_snapshot(result, _product(asin="OLD"), [])
    assert decision == "arbitrate"
