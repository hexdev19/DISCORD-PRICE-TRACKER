from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from typing import Any

from lxml import html as lxml_html

from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult

_PRODUCT_TYPES: tuple[str, ...] = ("Product", "IndividualProduct")
_BRAND_TYPES: tuple[str, ...] = ("Brand", "Organization")
_OFFER_TYPES: tuple[str, ...] = ("Offer", "AggregateOffer")


def extract_structured(html: str, *, region_hint: str | None = None) -> ScrapeResult:
    if not html:
        return ScrapeResult(status="failed", tier_used=1)

    try:
        tree = lxml_html.fromstring(html)
    except (ValueError, lxml_html.etree.ParserError):
        return ScrapeResult(status="failed", tier_used=1)

    fingerprint: dict[str, Any] = {}

    for product in _select_jsonld_products(tree):
        result = _from_jsonld(product, region_hint=region_hint)
        if result is not None:
            result.raw_fingerprint = {**fingerprint, **result.raw_fingerprint, "matched": "json-ld"}
            return result
        fingerprint["json-ld_seen"] = True

    microdata = _from_microdata(tree, region_hint=region_hint)
    if microdata is not None:
        microdata.raw_fingerprint = {
            **fingerprint,
            **microdata.raw_fingerprint,
            "matched": "microdata",
        }
        return microdata

    og = _from_opengraph(tree, region_hint=region_hint)
    if og is not None:
        og.raw_fingerprint = {**fingerprint, **og.raw_fingerprint, "matched": "opengraph"}
        return og

    return ScrapeResult(status="failed", tier_used=1, raw_fingerprint=fingerprint)


def _select_jsonld_products(tree: lxml_html.HtmlElement) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for script in tree.xpath('//script[@type="application/ld+json"]'):
        text = (script.text_content() or "").strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            continue
        candidates.extend(_collect_products(data))
    with_offers = [node for node in candidates if node.get("offers")]
    return with_offers or candidates


def _collect_products(node: Any) -> Iterator[dict[str, Any]]:
    if isinstance(node, list):
        for item in node:
            yield from _collect_products(item)
        return
    if not isinstance(node, dict):
        return
    if _matches_type(node.get("@type"), _PRODUCT_TYPES):
        yield node
    graph = node.get("@graph")
    if isinstance(graph, list):
        for item in graph:
            yield from _collect_products(item)


def _matches_type(types: Any, names: Sequence[str]) -> bool:
    lowered = {n.lower() for n in names}
    if isinstance(types, str):
        return types.lower() in lowered
    if isinstance(types, list):
        return any(isinstance(t, str) and t.lower() in lowered for t in types)
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

    status = (
        "ok" if price is not None and (in_stock is not None or currency is not None) else "partial"
    )
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
        raw_fingerprint={"price_text": price_raw},
    )


def _offer_fields(offers: Any) -> tuple[str | None, str | None, str | None]:
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None, None, None
    price = offers.get("price") or offers.get("lowPrice") or offers.get("highPrice")
    currency = offers.get("priceCurrency") or offers.get("currency")
    availability = offers.get("availability")
    return _coerce_str(price), _coerce_str(currency), _coerce_str(availability)


def _from_microdata(tree: lxml_html.HtmlElement, *, region_hint: str | None) -> ScrapeResult | None:
    scope = _pick_product_scope(_find_product_scopes(tree))
    if scope is None:
        return None

    title = _direct_itemprop(scope, "name")
    image = _direct_itemprop(scope, "image", attr="src") or _direct_itemprop(scope, "image")

    brand_scope = _find_subscope(scope, "brand", _BRAND_TYPES)
    brand = (
        _direct_itemprop(brand_scope, "name")
        if brand_scope is not None
        else _direct_itemprop(scope, "brand")
    )

    offer_scope = _find_subscope(scope, "offers", _OFFER_TYPES)
    offer = offer_scope if offer_scope is not None else scope
    price_raw = _direct_itemprop(offer, "price", attr="content") or _direct_itemprop(offer, "price")
    currency_raw = _direct_itemprop(offer, "priceCurrency", attr="content") or _direct_itemprop(
        offer, "priceCurrency"
    )
    avail = _direct_itemprop(offer, "availability", attr="href") or _direct_itemprop(
        offer, "availability"
    )

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
        raw_fingerprint={"price_text": price_raw},
    )


def _find_product_scopes(tree: lxml_html.HtmlElement) -> list[lxml_html.HtmlElement]:
    nodes: list[lxml_html.HtmlElement] = tree.xpath(
        "//*[@itemscope and ("
        'contains(@itemtype, "schema.org/Product")'
        ' or contains(@itemtype, "schema.org/IndividualProduct"))]'
    )
    return nodes


def _pick_product_scope(
    scopes: Sequence[lxml_html.HtmlElement],
) -> lxml_html.HtmlElement | None:
    if not scopes:
        return None
    for scope in scopes:
        if _find_subscope(scope, "offers", _OFFER_TYPES) is not None:
            return scope
    return scopes[0]


def _find_subscope(
    scope: lxml_html.HtmlElement, prop: str, type_suffixes: Sequence[str]
) -> lxml_html.HtmlElement | None:
    for el in _direct_itemprop_nodes(scope, prop):
        if el.get("itemscope") is None:
            continue
        itemtype = el.get("itemtype") or ""
        if any(itemtype.rsplit("/", 1)[-1] == suffix for suffix in type_suffixes):
            return el
    return None


def _direct_itemprop(
    scope: lxml_html.HtmlElement, name: str, *, attr: str | None = None
) -> str | None:
    for el in _direct_itemprop_nodes(scope, name):
        if attr is not None:
            text = _coerce_str(el.get(attr))
            if text:
                return text
            continue
        text = _coerce_str(el.get("content")) or _coerce_str(el.text_content())
        if text:
            return text
    return None


def _direct_itemprop_nodes(scope: lxml_html.HtmlElement, name: str) -> list[lxml_html.HtmlElement]:
    return [
        el
        for el in scope.xpath(f'.//*[@itemprop="{name}"]')
        if _nearest_itemscope(el, scope) is scope
    ]


def _nearest_itemscope(
    el: lxml_html.HtmlElement, root: lxml_html.HtmlElement
) -> lxml_html.HtmlElement:
    parent = el.getparent()
    while parent is not None and parent is not root:
        if parent.get("itemscope") is not None:
            return parent
        parent = parent.getparent()
    return root


def _from_opengraph(tree: lxml_html.HtmlElement, *, region_hint: str | None) -> ScrapeResult | None:
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
        raw_fingerprint={"price_text": price_raw},
    )


def _meta_map(tree: lxml_html.HtmlElement) -> dict[str, str]:
    out: dict[str, str] = {}
    for el in tree.xpath("//meta"):
        key = el.get("property") or el.get("name")
        content = el.get("content")
        if key and content:
            out[key.lower()] = content
    return out


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


__all__ = ["extract_structured"]
