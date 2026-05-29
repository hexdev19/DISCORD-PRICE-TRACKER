from __future__ import annotations

import re

from lxml import html as lxml_html

from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult

_PRICE_TEXT_RE = re.compile(
    r"(?P<sym>[$€£¥₹₽₩₺]|[A-Z]{3})?\s*"
    r"(?P<num>\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)"
    r"\s*(?P<code>[A-Z]{3})?"
)
_PRICE_CLASS_RE = re.compile(r"\b(price|amount|cost|now|sale)\b", re.IGNORECASE)
_STOCK_CLASS_RE = re.compile(r"\b(stock|availability|sold[-_ ]?out)\b", re.IGNORECASE)


def auto_extract(html: str, *, region_hint: str | None = None) -> ScrapeResult:
    if not html:
        return ScrapeResult(status="failed", tier_used=2)
    try:
        tree = lxml_html.fromstring(html)
    except (ValueError, lxml_html.etree.ParserError):
        return ScrapeResult(status="failed", tier_used=2)

    candidates = _price_candidates(tree)
    if not candidates:
        return ScrapeResult(status="failed", tier_used=2)

    candidates.sort(key=lambda c: c[0], reverse=True)
    best_score, raw_text, currency_token = candidates[0]

    price = parse_price(raw_text)
    currency = parse_currency(currency_token, region_hint=region_hint)
    if price is None:
        return ScrapeResult(status="failed", tier_used=2)

    title = _first_text(tree, "//h1") or _meta(tree, "og:title")
    image = _meta(tree, "og:image")
    in_stock = _stock_signal(tree)

    parsed = [parse_price(c[1]) for c in candidates]
    price_candidates = sorted({float(p) for p in parsed if p is not None})

    status = "ok" if best_score >= 3 and currency is not None else "partial"
    return ScrapeResult(
        status=status,
        tier_used=2,
        title=title,
        image_url=image,
        price=price,
        currency=currency,
        in_stock=in_stock,
        region_hint=region_hint,
        raw_fingerprint={
            "score": best_score,
            "matched": "heuristic",
            "price_text": raw_text,
            "price_candidates": price_candidates,
        },
    )


def _price_candidates(
    tree: lxml_html.HtmlElement,
) -> list[tuple[int, str, str | None]]:
    results: list[tuple[int, str, str | None]] = []
    for el in tree.xpath("//*[@itemprop or @class or @data-price]"):
        score = 0
        if el.get("itemprop") == "price":
            score += 5
        cls = el.get("class") or ""
        if _PRICE_CLASS_RE.search(cls):
            score += 2
        data_price = el.get("data-price")
        if data_price:
            score += 3
        if score == 0:
            continue
        text = (el.get("content") or data_price or el.text_content() or "").strip()
        if not text:
            continue
        match = _PRICE_TEXT_RE.search(text)
        if not match:
            continue
        results.append((score, match.group("num"), match.group("sym") or match.group("code")))
    return results


def _stock_signal(tree: lxml_html.HtmlElement) -> bool | None:
    for el in tree.xpath("//*[@itemprop='availability']"):
        v = el.get("href") or el.get("content") or el.text_content() or ""
        stock = parse_stock(v)
        if stock is not None:
            return stock
    for el in tree.xpath("//*[@class]"):
        cls = el.get("class") or ""
        if not _STOCK_CLASS_RE.search(cls):
            continue
        stock = parse_stock(el.text_content() or "")
        if stock is not None:
            return stock
    return None


def _first_text(tree: lxml_html.HtmlElement, xpath: str) -> str | None:
    nodes = tree.xpath(xpath)
    if not nodes:
        return None
    text = nodes[0].text_content().strip()
    return text or None


def _meta(tree: lxml_html.HtmlElement, prop: str) -> str | None:
    for el in tree.xpath(f'//meta[@property="{prop}" or @name="{prop}"]'):
        v = el.get("content")
        if v:
            return v.strip()
    return None


__all__ = ["auto_extract"]
