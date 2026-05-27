from __future__ import annotations

import re

from app.scraper.adapters.base import parse_html, register
from app.scraper.normalize import parse_currency, parse_price
from app.scraper.schemas import ScrapeResult
from app.scraper.structured import extract_structured


class AliExpressAdapter:
    domain_match = re.compile(r"^(?:www\.)?aliexpress\.(com|us|ru)$")
    needs_browser = True

    async def extract(
        self,
        url: str,
        html: str | None,
        rendered_html: str | None,
    ) -> ScrapeResult:
        payload = rendered_html or html
        if not payload:
            return ScrapeResult(status="failed", tier_used=3)

        structured = extract_structured(payload)
        if structured.is_ok:
            structured.tier_used = 3
            return structured

        tree = parse_html(payload)
        if tree is None:
            return ScrapeResult(status="failed", tier_used=3)

        title = _first_text(tree, '//h1') or _first_text(tree, '//*[@class="product-title"]')
        price_text = _first_text(tree, '//*[contains(@class, "product-price-value")]')
        price = parse_price(price_text)
        currency = parse_currency(price_text)

        if price is None:
            return ScrapeResult(status="failed", tier_used=3, title=title)

        return ScrapeResult(
            status="ok" if currency is not None else "partial",
            tier_used=3,
            title=title,
            price=price,
            currency=currency,
            raw_fingerprint={"matched": "aliexpress-dom"},
        )


def _first_text(tree: object, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    text = (nodes[0].text_content() or "").strip()
    return text or None


register(AliExpressAdapter())
