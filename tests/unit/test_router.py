from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.scraper.circuit import InMemoryCircuitBreaker
from app.scraper.router import RouterDeps, TierRouter

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _struct_fixture(name: str) -> str:
    return (FIXTURES / "structured" / name).read_text(encoding="utf-8")


def _adapter_fixture(name: str) -> str:
    return (FIXTURES / "adapters" / name / "example.html").read_text(encoding="utf-8")


def make_router(
    *,
    html: str | None = None,
    rendered: str | None = None,
    fetch_raises: Exception | None = None,
) -> tuple[TierRouter, InMemoryCircuitBreaker]:
    async def fetch(_url: str) -> str:
        if fetch_raises:
            raise fetch_raises
        return html or ""

    async def render(_url: str) -> str | None:
        return rendered

    cb = InMemoryCircuitBreaker()
    router = TierRouter(RouterDeps(fetch_html=fetch, render_page=render, circuit=cb))
    return router, cb


async def test_tier1_wins_when_structured_data_present() -> None:
    router, cb = make_router(html=_struct_fixture("jsonld_full.html"))
    result = await router.scrape("https://acme.example/p/1")
    assert result.status == "ok"
    assert result.tier_used == 1
    assert result.price == Decimal("29.99")
    assert await cb.state("acme.example") == "closed"


async def test_tier3_adapter_runs_for_known_host() -> None:
    router, _ = make_router(html=_adapter_fixture("amazon"))
    result = await router.scrape("https://www.amazon.com/dp/B09XS7JWHH")
    assert result.status == "ok"
    assert result.tier_used in (1, 3)
    assert result.asin == "B09XS7JWHH"


async def test_failed_fetch_records_failure_and_returns_failed() -> None:
    router, cb = make_router(fetch_raises=RuntimeError("network"))
    result = await router.scrape("https://acme.example/p/2")
    assert result.status == "failed"
    assert await cb.state("acme.example") in ("closed", "open")


async def test_open_circuit_short_circuits_request() -> None:
    router, cb = make_router(html=_struct_fixture("jsonld_full.html"))
    for _ in range(10):
        await cb.record_failure("acme.example")

    result = await router.scrape("https://acme.example/p/3")
    assert result.status == "failed"
    assert result.error is not None and result.error.code == "circuit_open"


async def test_browser_needed_host_uses_rendered_html() -> None:
    router, _ = make_router(
        html=None,
        rendered=_adapter_fixture("aliexpress"),
    )
    result = await router.scrape("https://www.aliexpress.com/item/1.html")
    assert result.status == "ok"
    assert result.tier_used in (3, 4)
    assert result.price == Decimal("12.99")
