from __future__ import annotations

from decimal import Decimal

import pytest

from app.scraper.normalize import parse_currency, parse_price, parse_stock


class TestParsePrice:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("$349.99", Decimal("349.99")),
            ("349.99", Decimal("349.99")),
            ("1,234.56", Decimal("1234.56")),
            ("1.234,56", Decimal("1234.56")),
            ("EUR 99,00", Decimal("99.00")),
            ("12.345", Decimal("12345.00")),
            ("12,99", Decimal("12.99")),
        ],
    )
    def test_parses_known_formats(self, raw: str, expected: Decimal) -> None:
        assert parse_price(raw) == expected

    @pytest.mark.parametrize("raw", ["", None, "free", "0.00", "9999999"])
    def test_rejects_invalid_or_out_of_range(self, raw: str | None) -> None:
        assert parse_price(raw) is None


class TestParseCurrency:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("$", "USD"),
            ("US$", "USD"),
            ("€", "EUR"),
            ("£", "GBP"),
            ("USD", "USD"),
            ("eur", "EUR"),
            ("$349.99", "USD"),
        ],
    )
    def test_known_symbols_and_codes(self, raw: str, expected: str) -> None:
        assert parse_currency(raw) == expected

    def test_uses_region_default(self) -> None:
        assert parse_currency(None, region_hint="GB") == "GBP"
        assert parse_currency(None, region_hint="DE") == "EUR"

    def test_unknown_no_region_returns_none(self) -> None:
        assert parse_currency(None) is None
        assert parse_currency("???") is None


class TestParseStock:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("https://schema.org/InStock", True),
            ("InStock", True),
            ("in stock", True),
            ("Out of stock", False),
            ("https://schema.org/OutOfStock", False),
            ("sold out", False),
            ("", None),
            ("?", None),
            (None, None),
        ],
    )
    def test_signals(self, raw: str | None, expected: bool | None) -> None:
        assert parse_stock(raw) is expected
