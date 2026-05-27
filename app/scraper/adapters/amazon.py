from __future__ import annotations

import re
from urllib.parse import urlsplit

from app.scraper.adapters.base import parse_html, register
from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult
from app.scraper.structured import extract_structured

_ASIN_RE = re.compile(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})(?:[/?]|$)")
_TLD_TO_REGION: dict[str, str] = {
    "com": "US",
    "co.uk": "GB",
    "de": "DE",
    "fr": "FR",
    "it": "IT",
    "es": "ES",
    "ca": "CA",
    "com.mx": "MX",
}


class AmazonAdapter:
    domain_match = re.compile(
        r"^(?:www\.)?amazon\.(com|co\.uk|de|fr|it|es|ca|com\.mx)$"
    )
    needs_browser = False

    async def extract(
        self,
        url: str,
        html: str | None,
        rendered_html: str | None,
    ) -> ScrapeResult:
        host = urlsplit(url).hostname or ""
        region = _region_from_host(host)
        asin = _asin_from_url(url)

        payload = rendered_html or html
        if not payload:
            return ScrapeResult(status="failed", tier_used=3, region_hint=region, asin=asin)

        structured = extract_structured(payload, region_hint=region)
        if structured.is_ok:
            structured.tier_used = 3
            structured.asin = asin or structured.asin
            return structured

        tree = parse_html(payload)
        if tree is None:
            return ScrapeResult(status="failed", tier_used=3, region_hint=region, asin=asin)

        title = _first_text(tree, '//*[@id="productTitle"]')
        price_text = _first_text(
            tree, '//*[contains(@class, "a-price")]//*[contains(@class, "a-offscreen")]'
        )
        price = parse_price(price_text)
        currency = parse_currency(price_text, region_hint=region)
        avail = _first_text(tree, '//*[@id="availability"]')
        image = _attr(tree, '//*[@id="landingImage"]', "src") or _attr(
            tree, '//*[@id="landingImage"]', "data-old-hires"
        )

        if price is None:
            return ScrapeResult(
                status="failed",
                tier_used=3,
                title=title,
                image_url=image,
                region_hint=region,
                asin=asin,
            )

        return ScrapeResult(
            status="ok" if currency is not None else "partial",
            tier_used=3,
            title=title,
            image_url=image,
            price=price,
            currency=currency,
            in_stock=parse_stock(avail),
            region_hint=region,
            asin=asin,
            raw_fingerprint={"matched": "amazon-dom"},
        )


def _region_from_host(host: str) -> str | None:
    host = host.lower().removeprefix("www.")
    if not host.startswith("amazon."):
        return None
    tld = host[len("amazon.") :]
    return _TLD_TO_REGION.get(tld)


def _asin_from_url(url: str) -> str | None:
    match = _ASIN_RE.search(url)
    return match.group(1) if match else None


def _first_text(tree: object, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    text = (nodes[0].text_content() or "").strip()
    return text or None


def _attr(tree: object, xpath: str, name: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    value = nodes[0].get(name)
    return value.strip() if value else None


register(AmazonAdapter())
