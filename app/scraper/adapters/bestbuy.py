from __future__ import annotations

import re

from app.scraper.adapters.base import parse_html, register
from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult
from app.scraper.structured import extract_structured


class BestBuyAdapter:
    domain_match = re.compile(r"^(?:www\.)?bestbuy\.com$")
    needs_browser = False

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

        title = _first_text(tree, '//h1.heading-5') or _first_text(tree, '//h1')
        price_text = _first_text(tree, '//*[@data-testid="customer-price"]') or _first_text(
            tree, '//*[contains(@class, "priceView-hero-price")]'
        )
        price = parse_price(price_text)
        currency = parse_currency(price_text, region_hint="US") or "USD"
        avail = _first_text(tree, '//*[contains(@class, "fulfillment-add-to-cart-button")]')

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
            raw_fingerprint={"matched": "bestbuy-dom"},
        )


def _first_text(tree: object, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    text = (nodes[0].text_content() or "").strip()
    return text or None


register(BestBuyAdapter())
