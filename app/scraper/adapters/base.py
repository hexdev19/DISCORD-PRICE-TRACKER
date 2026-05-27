"""Adapter contract and registry.

Adapters are stateless. Each one declares a regex its host must match
and whether it needs the Tier-4 browser session. The router picks the
first registered adapter whose ``domain_match`` accepts the URL's host.
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from app.scraper.schemas import ScrapeResult


class SiteAdapter(Protocol):
    domain_match: re.Pattern[str]
    needs_browser: bool

    async def extract(
        self,
        url: str,
        html: str | None,
        rendered_html: str | None,
    ) -> ScrapeResult: ...


_REGISTRY: list[SiteAdapter] = []


def register(adapter: SiteAdapter) -> SiteAdapter:
    _REGISTRY.append(adapter)
    return adapter


def find_adapter(host: str) -> SiteAdapter | None:
    for adapter in _REGISTRY:
        if adapter.domain_match.search(host):
            return adapter
    return None


def registered_adapters() -> tuple[SiteAdapter, ...]:
    return tuple(_REGISTRY)


def _reset_registry_for_tests() -> None:
    _REGISTRY.clear()


def _import_all() -> None:
    from app.scraper.adapters import (  # noqa: F401  (import side-effect = registration)
        aliexpress,
        amazon,
        bestbuy,
        ebay,
        target,
        walmart,
    )

    _ = (aliexpress, amazon, bestbuy, ebay, target, walmart)


def parse_html(html: str | None) -> Any | None:
    if not html:
        return None
    from lxml import html as lxml_html

    try:
        return lxml_html.fromstring(html)
    except (ValueError, lxml_html.etree.ParserError):
        return None
