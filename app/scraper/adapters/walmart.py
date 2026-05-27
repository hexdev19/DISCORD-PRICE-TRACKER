from __future__ import annotations

import re

from app.scraper.adapters.base import parse_html, register
from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult
from app.scraper.structured import extract_structured


class WalmartAdapter:
    domain_match = re.compile(r"^(?:www\.)?walmart\.com$")
    needs_browser = True

    async def extract(
        self,
        url: str,
        html: str | None,
        rendered_html: str | None,
    ) -> ScrapeResult:
        payload = rendered_html or html
        if not payload:
            return ScrapeResult(status="failed", tier_used=3, region_hint="US")

        structured = extract_structured(payload, region_hint="US")
        if structured.is_ok:
            structured.tier_used = 3
            return structured

        tree = parse_html(payload)
        if tree is None:
            return ScrapeResult(status="failed", tier_used=3, region_hint="US")

        title = _first_text(tree, '//h1[@itemprop="name"]') or _first_text(tree, '//h1')
        price_text = _first_text(tree, '//*[@itemprop="price"]') or _first_text(
            tree, '//*[@data-automation-id="product-price"]'
        )
        price = parse_price(price_text)
        currency = parse_currency(price_text, region_hint="US") or "USD"
        avail = _first_text(tree, '//*[@data-automation-id="add-to-cart"]')

        if price is None:
            return ScrapeResult(status="failed", tier_used=3, title=title, region_hint="US")

        return ScrapeResult(
            status="ok",
            tier_used=3,
            title=title,
            price=price,
            currency=currency,
            in_stock=parse_stock(avail) if avail else None,
            region_hint="US",
            raw_fingerprint={"matched": "walmart-dom"},
        )


def _first_text(tree: object, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    text = (nodes[0].text_content() or "").strip()
    return text or None


register(WalmartAdapter())
