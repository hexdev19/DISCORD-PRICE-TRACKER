from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.config.limits import AI_FALLBACK_TIMEOUT_MS
from app.config.settings import get_settings
from app.models.price_snapshot import PriceSnapshot
from app.models.product import Product
from app.scraper.normalize import parse_currency, parse_price, parse_stock
from app.scraper.schemas import ScrapeResult, ScrapeStatus
from app.services.scrape_validation import validate_snapshot
from app.utils.logger import get_logger

log = get_logger(__name__)

AI_TIER = 5

_MISSING_PROMPT = (
    "Extract the current price, currency (ISO 4217 code), in-stock status, and "
    "title for the product on this page. Use only what is shown on the page; "
    "return null for anything that is absent. Do not guess or invent a price. "
    'Respond with JSON: {"title": string|null, "price": number|null, '
    '"currency": string|null, "in_stock": boolean|null}.'
)


def _arbitration_prompt(result: ScrapeResult, product: Product) -> str:
    return (
        "We scraped this page and are unsure the data is correct.\n"
        f"Expected product: {product.title or 'unknown'} "
        f"(currency {product.currency or 'unknown'}).\n"
        f"We found: price={result.price}, currency={result.currency}, "
        f"in_stock={result.in_stock}, title={result.title}.\n"
        "Confirm the real current price for THIS exact product from the page, and "
        "whether the page actually shows this product. Use only values shown on the "
        "page; do not guess or invent a price; return null if the value is absent.\n"
        'Respond with JSON: {"title": string|null, "price": number|null, '
        '"currency": string|null, "in_stock": boolean|null, "is_right_product": boolean}.'
    )


def _coerce_stock(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return parse_stock(str(value))


def _to_result(data: dict[str, Any], *, region_hint: str | None) -> ScrapeResult:
    if data.get("is_right_product") is False:
        return ScrapeResult(status="failed", tier_used=AI_TIER, flags=["ai_wrong_product"])
    raw_price = data.get("price")
    price = parse_price(str(raw_price)) if raw_price is not None else None
    currency = parse_currency(data.get("currency"), region_hint=region_hint)
    in_stock = _coerce_stock(data.get("in_stock"))
    title = data.get("title") if isinstance(data.get("title"), str) else None
    status: ScrapeStatus = "ok" if price is not None else "partial"
    return ScrapeResult(
        status=status,
        tier_used=AI_TIER,
        title=title,
        price=price,
        currency=currency,
        in_stock=in_stock,
        region_hint=region_hint,
    )


def _extract_json(result: Any) -> dict[str, Any] | None:
    data = getattr(result, "json", None)
    if data is None and isinstance(result, dict):
        data = result.get("json")
    return data if isinstance(data, dict) else None


async def ai_extract(
    url: str,
    product: Product,
    snapshots: Sequence[PriceSnapshot],
    *,
    prior: ScrapeResult | None = None,
) -> ScrapeResult | None:
    settings = get_settings()
    if not settings.firecrawl_api_key:
        log.info("ai_extract.skipped_no_key", url=url)
        return None
    try:
        from firecrawl import Firecrawl
    except ImportError:
        log.warning("ai_extract.skipped_import_failed", url=url)
        return None

    prompt = _arbitration_prompt(prior, product) if prior is not None else _MISSING_PROMPT
    try:
        raw = Firecrawl(api_key=settings.firecrawl_api_key).scrape(
            url,
            formats=[{"type": "json", "prompt": prompt}],
            only_main_content=False,
            timeout=AI_FALLBACK_TIMEOUT_MS,
        )
    except Exception as exc:
        log.warning("ai_extract.failed", url=url, error=str(exc))
        return None

    data = _extract_json(raw)
    if data is None:
        log.warning("ai_extract.no_json", url=url)
        return None

    result = _to_result(data, region_hint=product.region)
    confidence, flags, decision = validate_snapshot(result, product, snapshots)
    result.confidence = confidence
    result.flags = flags
    log.info(
        "ai_extract.result",
        url=url,
        price=str(result.price),
        confidence=confidence,
        decision=decision,
        flags=flags,
    )
    return result


__all__ = ["AI_TIER", "ai_extract"]
