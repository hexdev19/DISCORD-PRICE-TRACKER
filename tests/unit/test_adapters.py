from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.scraper.adapters import find_adapter
from app.scraper.adapters.aliexpress import AliExpressAdapter
from app.scraper.adapters.amazon import AmazonAdapter
from app.scraper.adapters.bestbuy import BestBuyAdapter
from app.scraper.adapters.ebay import EBayAdapter
from app.scraper.adapters.target import TargetAdapter
from app.scraper.adapters.walmart import WalmartAdapter

FIXTURES = Path(__file__).parent.parent / "fixtures" / "adapters"


def _load(name: str) -> str:
    return (FIXTURES / name / "example.html").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "host,expected_cls",
    [
        ("www.amazon.com", AmazonAdapter),
        ("amazon.co.uk", AmazonAdapter),
        ("amazon.de", AmazonAdapter),
        ("ebay.com", EBayAdapter),
        ("aliexpress.com", AliExpressAdapter),
        ("walmart.com", WalmartAdapter),
        ("bestbuy.com", BestBuyAdapter),
        ("target.com", TargetAdapter),
    ],
)
def test_registry_dispatch(host: str, expected_cls: type) -> None:
    adapter = find_adapter(host)
    assert adapter is not None and isinstance(adapter, expected_cls)


def test_registry_returns_none_for_unknown_host() -> None:
    assert find_adapter("unknown.example") is None


async def test_amazon_extracts_from_jsonld_and_url() -> None:
    adapter = AmazonAdapter()
    result = await adapter.extract(
        "https://www.amazon.com/dp/B09XS7JWHH/",
        _load("amazon"),
        None,
    )
    assert result.status == "ok"
    assert result.tier_used == 3
    assert result.price == Decimal("349.99")
    assert result.currency == "USD"
    assert result.asin == "B09XS7JWHH"
    assert result.region_hint == "US"


async def test_ebay_extracts_from_dom_and_item_id() -> None:
    adapter = EBayAdapter()
    result = await adapter.extract(
        "https://www.ebay.com/itm/nintendo-switch/123456789012",
        _load("ebay"),
        None,
    )
    assert result.price == Decimal("299.99")
    assert result.currency == "USD"
    assert result.mpn == "123456789012"
    assert result.tier_used == 3


async def test_aliexpress_extracts_from_dom() -> None:
    adapter = AliExpressAdapter()
    result = await adapter.extract(
        "https://www.aliexpress.com/item/1005006.html",
        _load("aliexpress"),
        None,
    )
    assert result.price == Decimal("12.99")
    assert result.currency == "USD"
    assert result.tier_used == 3


async def test_walmart_extracts_from_microdata_dom() -> None:
    adapter = WalmartAdapter()
    result = await adapter.extract(
        "https://www.walmart.com/ip/lego/123",
        _load("walmart"),
        None,
    )
    assert result.price == Decimal("24.99")
    assert result.currency == "USD"
    assert result.tier_used == 3


async def test_bestbuy_extracts_from_data_testid() -> None:
    adapter = BestBuyAdapter()
    result = await adapter.extract(
        "https://www.bestbuy.com/site/sample/123.p",
        _load("bestbuy"),
        None,
    )
    assert result.price == Decimal("499.99")
    assert result.currency == "USD"
    assert result.tier_used == 3


async def test_target_extracts_from_data_test() -> None:
    adapter = TargetAdapter()
    result = await adapter.extract(
        "https://www.target.com/p/coffee/-/A-12345",
        _load("target"),
        None,
    )
    assert result.price == Decimal("59.99")
    assert result.currency == "USD"
    assert result.tier_used == 3
