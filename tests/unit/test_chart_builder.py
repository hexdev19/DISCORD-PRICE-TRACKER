from __future__ import annotations

from decimal import Decimal

from app.utils.chart_builder import sparkline


def test_empty_yields_dash() -> None:
    assert sparkline([]) == "—"
    assert sparkline([None, None]) == "—"


def test_flat_series_uses_middle_block() -> None:
    out = sparkline([Decimal("5"), Decimal("5"), Decimal("5")])
    assert len(out) == 3
    assert set(out) == {"▅"}


def test_ascending_series_spans_blocks() -> None:
    out = sparkline([1, 2, 3, 4, 5, 6, 7, 8])
    assert out[0] == "▁"
    assert out[-1] == "█"
    assert len(out) == 8


def test_none_renders_as_space() -> None:
    out = sparkline([1, None, 2])
    assert len(out) == 3
    assert out[1] == " "
