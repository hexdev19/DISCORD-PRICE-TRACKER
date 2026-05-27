from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable
from urllib.parse import urlsplit

from app.scraper import autoextract, structured
from app.scraper.adapters import find_adapter
from app.scraper.adapters.base import SiteAdapter
from app.scraper.circuit import CircuitBreaker
from app.scraper.schemas import ScrapeError, ScrapeResult
from app.utils.logger import get_logger

log = get_logger(__name__)

HtmlFetcher = Callable[[str], Awaitable[str]]
PageRenderer = Callable[[str], Awaitable[str | None]]


@dataclass(slots=True)
class RouterDeps:
    fetch_html: HtmlFetcher
    render_page: PageRenderer
    circuit: CircuitBreaker


class TierRouter:
    def __init__(self, deps: RouterDeps) -> None:
        self._deps = deps

    async def scrape(self, url: str, *, region_hint: str | None = None) -> ScrapeResult:
        domain = (urlsplit(url).hostname or "").lower()
        if not domain:
            return ScrapeResult(
                status="failed",
                tier_used=0,
                error=ScrapeError(code="invalid_response", message="missing host"),
            )

        state = await self._deps.circuit.state(domain)
        if state == "open":
            log.info("scrape.skipped", domain=domain, reason="circuit_open")
            return ScrapeResult(
                status="failed",
                tier_used=0,
                error=ScrapeError(code="circuit_open"),
            )

        adapter = find_adapter(domain)

        if adapter is None or not adapter.needs_browser:
            html = await self._safe_fetch(url, domain)
            if html is not None:
                t1 = structured.extract_structured(html, region_hint=region_hint)
                if t1.is_ok:
                    await self._deps.circuit.record_success(domain)
                    log.info("scrape.end", domain=domain, tier=1, status="ok")
                    return t1

                t2 = autoextract.auto_extract(html, region_hint=region_hint)
                if t2.is_ok:
                    await self._deps.circuit.record_success(domain)
                    log.info("scrape.end", domain=domain, tier=2, status="ok")
                    return t2

                if adapter is not None:
                    t3 = await self._run_adapter(adapter, url, html=html, rendered=None)
                    if t3.is_ok:
                        await self._deps.circuit.record_success(domain)
                        log.info("scrape.end", domain=domain, tier=3, status="ok")
                        return t3

        if adapter is not None and adapter.needs_browser:
            rendered = await self._safe_render(url, domain)
            if rendered is not None:
                t4 = await self._run_adapter(adapter, url, html=None, rendered=rendered)
                if t4.is_ok:
                    await self._deps.circuit.record_success(domain)
                    log.info("scrape.end", domain=domain, tier=4, status="ok")
                    return t4
                t4_struct = structured.extract_structured(rendered, region_hint=region_hint)
                if t4_struct.is_ok:
                    t4_struct.tier_used = 4
                    await self._deps.circuit.record_success(domain)
                    log.info("scrape.end", domain=domain, tier=4, status="ok")
                    return t4_struct

        await self._deps.circuit.record_failure(domain)
        log.info("scrape.end", domain=domain, status="failed")
        if adapter is None:
            return ScrapeResult(
                status="failed",
                tier_used=2,
                error=ScrapeError(code="no_extractor"),
            )
        return ScrapeResult(
            status="failed",
            tier_used=4 if adapter.needs_browser else 3,
            error=ScrapeError(code="no_price"),
        )

    async def _safe_fetch(self, url: str, domain: str) -> str | None:
        try:
            return await self._deps.fetch_html(url)
        except Exception as exc:
            log.warning("scrape.fetch_failed", domain=domain, error=type(exc).__name__)
            return None

    async def _safe_render(self, url: str, domain: str) -> str | None:
        try:
            return await self._deps.render_page(url)
        except Exception as exc:
            log.warning("scrape.render_failed", domain=domain, error=type(exc).__name__)
            return None

    async def _run_adapter(
        self,
        adapter: SiteAdapter,
        url: str,
        *,
        html: str | None,
        rendered: str | None,
    ) -> ScrapeResult:
        try:
            return await adapter.extract(url, html, rendered)
        except Exception as exc:
            log.warning(
                "scrape.adapter_failed",
                adapter=type(adapter).__name__,
                error=type(exc).__name__,
            )
            return ScrapeResult(
                status="failed",
                tier_used=4 if adapter.needs_browser else 3,
                error=ScrapeError(code="invalid_response", message=type(exc).__name__),
            )
