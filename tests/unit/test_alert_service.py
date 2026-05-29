from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.models.price_snapshot import PriceSnapshot
from app.models.watch import Watch
from app.services.alert_service import _rule_fires


def _watch(**rules: Any) -> Watch:
    return Watch(alert_rules=rules or {"drop": True})


def _snap(
    price: Decimal | None = None,
    in_stock: bool | None = True,
    confidence: float | None = None,
) -> PriceSnapshot:
    return PriceSnapshot(price=price, in_stock=in_stock, confidence=confidence)


def test_drop_fires_on_real_drop() -> None:
    prev = _snap(Decimal("100"))
    new = _snap(Decimal("80"))
    assert _rule_fires("drop", _watch(), prev, new) is True


def test_low_confidence_suppresses_drop() -> None:
    prev = _snap(Decimal("100"))
    new = _snap(Decimal("80"), confidence=0.2)
    assert _rule_fires("drop", _watch(), prev, new) is False


def test_low_confidence_suppresses_threshold() -> None:
    new = _snap(Decimal("50"), confidence=0.2)
    assert _rule_fires("threshold", _watch(threshold="60"), None, new) is False


def test_low_confidence_suppresses_restock() -> None:
    prev = _snap(Decimal("100"), in_stock=False)
    new = _snap(Decimal("100"), in_stock=True, confidence=0.2)
    assert _rule_fires("restock", _watch(restock=True), prev, new) is False


def test_confidence_none_is_back_compat() -> None:
    prev = _snap(Decimal("100"))
    new = _snap(Decimal("80"), confidence=None)
    assert _rule_fires("drop", _watch(), prev, new) is True


def test_high_confidence_allows_drop() -> None:
    prev = _snap(Decimal("100"))
    new = _snap(Decimal("80"), confidence=0.9)
    assert _rule_fires("drop", _watch(), prev, new) is True


def test_tiny_drop_below_min_ratio_suppressed() -> None:
    prev = _snap(Decimal("100.00"))
    new = _snap(Decimal("99.99"))
    assert _rule_fires("drop", _watch(), prev, new) is False


def test_drop_meeting_min_ratio_fires() -> None:
    prev = _snap(Decimal("100.00"))
    new = _snap(Decimal("98.00"))
    assert _rule_fires("drop", _watch(), prev, new) is True


def test_restock_needs_price() -> None:
    prev = _snap(Decimal("100"), in_stock=False)
    new_no_price = _snap(None, in_stock=True)
    new_with_price = _snap(Decimal("100"), in_stock=True)
    assert _rule_fires("restock", _watch(restock=True), prev, new_no_price) is False
    assert _rule_fires("restock", _watch(restock=True), prev, new_with_price) is True


def test_drop_not_fired_when_out_of_stock() -> None:
    prev = _snap(Decimal("100"))
    new = _snap(Decimal("80"), in_stock=False)
    assert _rule_fires("drop", _watch(), prev, new) is False


def test_threshold_fires_at_or_below() -> None:
    assert _rule_fires("threshold", _watch(threshold="60"), None, _snap(Decimal("60"))) is True
    assert _rule_fires("threshold", _watch(threshold="60"), None, _snap(Decimal("61"))) is False
