from __future__ import annotations

import sys
import types
from decimal import Decimal
from typing import Any, ClassVar

import pytest
from app.config.settings import Settings, get_settings
from app.models.product import Product
from app.services import ai_extract
from app.services.ai_extract import ai_extract as run_ai


class _FakeClient:
    last_kwargs: ClassVar[dict[str, Any]] = {}

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key

    def scrape(self, url: str, **kwargs: Any) -> Any:
        _FakeClient.last_kwargs = {"url": url, **kwargs}
        return types.SimpleNamespace(json=self.payload)


def _product(**kwargs: Any) -> Product:
    base: dict[str, Any] = {
        "source_url": "https://example.com/p",
        "domain": "example.com",
        "currency": "USD",
        "title": "Sony WH-1000XM5",
    }
    base.update(kwargs)
    return Product(**base)


def _install_settings(monkeypatch: pytest.MonkeyPatch, key: str | None) -> None:
    get_settings.cache_clear()

    def _fake() -> Settings:
        return Settings.model_construct(firecrawl_api_key=key)

    monkeypatch.setattr(ai_extract, "get_settings", _fake)


def _install_firecrawl(monkeypatch: pytest.MonkeyPatch, payload: Any) -> type[_FakeClient]:
    _FakeClient.payload = payload  # type: ignore[attr-defined]
    module = types.ModuleType("firecrawl")
    module.Firecrawl = _FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "firecrawl", module)
    return _FakeClient


async def test_skips_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, None)
    assert await run_ai("https://example.com/p", _product(), []) is None


async def test_skips_when_import_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    monkeypatch.setitem(sys.modules, "firecrawl", None)
    assert await run_ai("https://example.com/p", _product(), []) is None


async def test_maps_json_to_scrape_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    client = _install_firecrawl(
        monkeypatch,
        {"title": "Sony WH-1000XM5", "price": 299.99, "currency": "USD", "in_stock": True},
    )
    result = await run_ai("https://example.com/p", _product(), [])
    assert result is not None
    assert result.tier_used == ai_extract.AI_TIER
    assert result.price == Decimal("299.99")
    assert result.currency == "USD"
    assert result.in_stock is True
    assert result.status == "ok"
    assert client.last_kwargs["only_main_content"] is False
    assert client.last_kwargs["formats"][0]["type"] == "json"


async def test_missing_price_returns_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    _install_firecrawl(
        monkeypatch,
        {"title": None, "price": None, "currency": None, "in_stock": None},
    )
    result = await run_ai("https://example.com/p", _product(), [])
    assert result is not None
    assert result.price is None
    assert result.status == "partial"


async def test_wrong_product_flagged_and_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    _install_firecrawl(monkeypatch, {"price": 50, "is_right_product": False})
    result = await run_ai("https://example.com/p", _product(), [], prior=None)
    assert result is not None
    assert result.status == "failed"
    assert "ai_wrong_product" in result.flags


async def test_revalidation_flags_currency_flip(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    _install_firecrawl(
        monkeypatch,
        {"title": "Sony WH-1000XM5", "price": 299.99, "currency": "EUR", "in_stock": True},
    )
    result = await run_ai("https://example.com/p", _product(currency="USD"), [])
    assert result is not None
    assert "currency_flip" in result.flags
    assert result.confidence < 1.0


async def test_arbitration_prompt_used_when_prior_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_settings(monkeypatch, "fc-key")
    client = _install_firecrawl(
        monkeypatch,
        {"title": "Sony WH-1000XM5", "price": 100, "currency": "USD", "in_stock": True},
    )
    from app.scraper.schemas import ScrapeResult

    prior = ScrapeResult(status="ok", tier_used=1, price=Decimal("9999"), currency="USD")
    await run_ai("https://example.com/p", _product(), [], prior=prior)
    prompt = client.last_kwargs["formats"][0]["prompt"]
    assert "9999" in prompt
    assert "Sony WH-1000XM5" in prompt


async def test_no_json_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_settings(monkeypatch, "fc-key")
    _install_firecrawl(monkeypatch, None)
    assert await run_ai("https://example.com/p", _product(), []) is None
