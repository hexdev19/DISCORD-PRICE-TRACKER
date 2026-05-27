"""Tier 1 — structured-data extraction.

Reads JSON-LD ``Product`` blocks, microdata, RDFa, and OpenGraph from a
fetched HTML payload. Pure parsing; the actual HTTP fetch happens in the
router (Scrapling ``AsyncFetcher``).
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from lxml import html as lxml_html

from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult


def extract_structured(html: str, *, region_hint: str | None = None) -> ScrapeResult:
    if not html:
        return ScrapeResult(status="failed", tier_used=1)

    try:
        tree = lxml_html.fromstring(html)
    except (ValueError, lxml_html.etree.ParserError):
        return ScrapeResult(status="failed", tier_used=1)

    fingerprint: dict[str, Any] = {}

    for product in _iter_jsonld_products(tree):
        result = _from_jsonld(product, region_hint=region_hint)
        if result is not None:
            result.raw_fingerprint = {**fingerprint, "matched": "json-ld"}
            return result
        fingerprint["json-ld_seen"] = True

    microdata = _from_microdata(tree, region_hint=region_hint)
    if microdata is not None:
        microdata.raw_fingerprint = {**fingerprint, "matched": "microdata"}
        return microdata

    og = _from_opengraph(tree, region_hint=region_hint)
    if og is not None:
        og.raw_fingerprint = {**fingerprint, "matched": "opengraph"}
        return og

    return ScrapeResult(status="failed", tier_used=1, raw_fingerprint=fingerprint)


def _iter_jsonld_products(tree: lxml_html.HtmlElement) -> Iterator[dict[str, Any]]:
    for script in tree.xpath('//script[@type="application/ld+json"]'):
        text = (script.text_content() or "").strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        yield from _walk_for_product(data)


def _walk_for_product(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, dict):
        graph = node.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from _walk_for_product(item)
        types = node.get("@type")
        if _matches_product(types):
            yield node
        for v in node.values():
            if isinstance(v, (dict, list)) and v is not node.get("@graph"):
                yield from _walk_for_product(v)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_for_product(item)


def _matches_product(types: Any) -> bool:
    if isinstance(types, str):
        return types.lower() == "product"
    if isinstance(types, list):
        return any(isinstance(t, str) and t.lower() == "product" for t in types)
    return False


def _from_jsonld(node: dict[str, Any], *, region_hint: str | None) -> ScrapeResult | None:
    title = _coerce_str(node.get("name"))
    image = _first_str(node.get("image"))
    brand = _brand_str(node.get("brand"))
    gtin = _first_str(
        node.get("gtin13") or node.get("gtin12") or node.get("gtin8") or node.get("gtin")
    )
    mpn = _coerce_str(node.get("mpn"))

    price_raw, currency_raw, avail_raw = _offer_fields(node.get("offers"))
    price = parse_price(price_raw)
    currency = parse_currency(currency_raw, region_hint=region_hint)
    in_stock = parse_stock(avail_raw)

    if price is None and currency is None:
        return None

    status = "ok" if price is not None and (in_stock is not None or currency is not None) else "partial"
    return ScrapeResult(
        status=status,
        tier_used=1,
        title=title,
        image_url=image,
        brand=brand,
        price=price,
        currency=currency,
        in_stock=in_stock,
        gtin=gtin,
        mpn=mpn,
        region_hint=region_hint,
    )


def _offer_fields(offers: Any) -> tuple[str | None, str | None, str | None]:
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None, None, None
    price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
    currency = offers.get("priceCurrency") or offers.get("currency")
    availability = offers.get("availability")
    return (
        _coerce_str(price),
        _coerce_str(currency),
        _coerce_str(availability),
    )


def _from_microdata(
    tree: lxml_html.HtmlElement, *, region_hint: str | None
) -> ScrapeResult | None:
    scopes = tree.xpath(
        '//*[contains(@itemtype, "schema.org/Product") or contains(@itemtype, "schema.org/IndividualProduct")]'
    )
    if not scopes:
        return None
    scope = scopes[0]
    title = _itemprop(scope, "name")
    image = _itemprop(scope, "image", attr="src") or _itemprop(scope, "image")
    brand = _itemprop(scope, "brand")
    price_raw = _itemprop(scope, "price", attr="content") or _itemprop(scope, "price")
    currency_raw = _itemprop(scope, "priceCurrency", attr="content") or _itemprop(
        scope, "priceCurrency"
    )
    avail = _itemprop(scope, "availability", attr="href") or _itemprop(scope, "availability")

    price = parse_price(price_raw)
    currency = parse_currency(currency_raw, region_hint=region_hint)
    if price is None and currency is None:
        return None
    in_stock = parse_stock(avail)
    return ScrapeResult(
        status="ok" if price is not None and currency is not None else "partial",
        tier_used=1,
        title=title,
        image_url=image,
        brand=brand,
        price=price,
        currency=currency,
        in_stock=in_stock,
        region_hint=region_hint,
    )


def _from_opengraph(
    tree: lxml_html.HtmlElement, *, region_hint: str | None
) -> ScrapeResult | None:
    meta = _meta_map(tree)
    title = meta.get("og:title")
    image = meta.get("og:image")
    price_raw = meta.get("product:price:amount") or meta.get("og:price:amount")
    currency_raw = meta.get("product:price:currency") or meta.get("og:price:currency")
    avail = meta.get("product:availability") or meta.get("og:availability")

    price = parse_price(price_raw)
    currency = parse_currency(currency_raw, region_hint=region_hint)
    if price is None and currency is None and not title:
        return None
    in_stock = parse_stock(avail)
    status = "ok" if price is not None and currency is not None else "partial"
    return ScrapeResult(
        status=status,
        tier_used=1,
        title=title,
        image_url=image,
        price=price,
        currency=currency,
        in_stock=in_stock,
        region_hint=region_hint,
    )


def _meta_map(tree: lxml_html.HtmlElement) -> dict[str, str]:
    out: dict[str, str] = {}
    for el in tree.xpath("//meta"):
        key = el.get("property") or el.get("name")
        content = el.get("content")
        if key and content:
            out[key.lower()] = content
    return out


def _itemprop(
    scope: lxml_html.HtmlElement, name: str, *, attr: str | None = None
) -> str | None:
    matches = scope.xpath(f'.//*[@itemprop="{name}"]')
    if not matches:
        return None
    el = matches[0]
    if attr:
        val = el.get(attr)
        if val:
            return val.strip()
    val = el.get("content") or el.text_content()
    return val.strip() if val else None


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        v = value.strip()
        return v or None
    return None


def _first_str(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            s = _coerce_str(item)
            if s:
                return s
        return None
    return _coerce_str(value)


def _brand_str(value: Any) -> str | None:
    if isinstance(value, dict):
        return _coerce_str(value.get("name"))
    return _coerce_str(value)


_PRICE_PATTERN = re.compile(r"\b(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\b")
_FALLBACK_FIELDS: tuple[str, ...] = ("price", "amount", "cost")


def _has_price_signals(text: Iterable[str]) -> bool:
    return any(_PRICE_PATTERN.search(t) for t in text)


__all__ = ["extract_structured"]
