from __future__ import annotations

import re
from urllib.parse import urlsplit

from app.scraper.adapters.base import parse_html, register
from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult
from app.scraper.structured import extract_structured

_ITEM_ID_RE = re.compile(r"/itm/(?:[\w-]+/)?(\d{9,14})")
_TLD_TO_REGION = {"com": "US", "co.uk": "GB", "de": "DE"}


class EBayAdapter:
    domain_match = re.compile(r"^(?:www\.)?ebay\.(com|co\.uk|de)$")
    needs_browser = False

    async def extract(
        self,
        url: str,
        html: str | None,
        rendered_html: str | None,
    ) -> ScrapeResult:
        host = urlsplit(url).hostname or ""
        region = _region_from_host(host)
        item_id = _item_id(url)

        payload = rendered_html or html
        if not payload:
            return ScrapeResult(status="failed", tier_used=3, region_hint=region, mpn=item_id)

        structured = extract_structured(payload, region_hint=region)
        if structured.is_ok:
            structured.tier_used = 3
            structured.mpn = item_id or structured.mpn
            return structured

        tree = parse_html(payload)
        if tree is None:
            return ScrapeResult(status="failed", tier_used=3, region_hint=region, mpn=item_id)

        title = _first_text(tree, '//h1[contains(@class, "x-item-title")]') or _first_text(
            tree, '//*[@id="itemTitle"]'
        )
        price_text = _first_text(tree, '//*[contains(@class, "x-price-primary")]') or _first_text(
            tree, '//*[@id="prcIsum"]'
        )
        price = parse_price(price_text)
        currency = parse_currency(price_text, region_hint=region)
        avail = _first_text(tree, '//*[contains(@class, "d-quantity__availability")]')

        if price is None:
            return ScrapeResult(
                status="failed",
                tier_used=3,
                title=title,
                region_hint=region,
                mpn=item_id,
            )

        return ScrapeResult(
            status="ok" if currency is not None else "partial",
            tier_used=3,
            title=title,
            price=price,
            currency=currency,
            in_stock=parse_stock(avail),
            region_hint=region,
            mpn=item_id,
            raw_fingerprint={"matched": "ebay-dom"},
        )


def _region_from_host(host: str) -> str | None:
    host = host.lower().removeprefix("www.")
    if not host.startswith("ebay."):
        return None
    return _TLD_TO_REGION.get(host[len("ebay.") :])


def _item_id(url: str) -> str | None:
    match = _ITEM_ID_RE.search(url)
    return match.group(1) if match else None


def _first_text(tree: object, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)  # type: ignore[attr-defined]
    if not nodes:
        return None
    text = (nodes[0].text_content() or "").strip()
    return text or None


register(EBayAdapter())
