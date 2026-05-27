from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.config.limits import PRICE_MAX, PRICE_MIN

_PRICE_MIN_D = Decimal(PRICE_MIN)
_PRICE_MAX_D = Decimal(PRICE_MAX)

_SYMBOL_TO_ISO: dict[str, str] = {
    "$": "USD",
    "US$": "USD",
    "C$": "CAD",
    "CA$": "CAD",
    "A$": "AUD",
    "AU$": "AUD",
    "NZ$": "NZD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₽": "RUB",
    "R$": "BRL",
    "₩": "KRW",
    "₺": "TRY",
    "CHF": "CHF",
    "SEK": "SEK",
    "NOK": "NOK",
    "DKK": "DKK",
}

_REGION_DEFAULT_CURRENCY: dict[str, str] = {
    "US": "USD",
    "CA": "CAD",
    "GB": "GBP",
    "DE": "EUR",
    "FR": "EUR",
    "IT": "EUR",
    "ES": "EUR",
    "NL": "EUR",
    "BE": "EUR",
    "JP": "JPY",
    "AU": "AUD",
    "NZ": "NZD",
    "IN": "INR",
    "BR": "BRL",
    "MX": "MXN",
    "KR": "KRW",
}

_IN_STOCK_TOKENS = (
    "instock",
    "in_stock",
    "in stock",
    "available",
    "preorder",
    "limitedavailability",
)
_OUT_OF_STOCK_TOKENS = (
    "outofstock",
    "out_of_stock",
    "out of stock",
    "sold out",
    "soldout",
    "unavailable",
    "discontinued",
    "backorder",
)


def parse_currency(raw: str | None, *, region_hint: str | None = None) -> str | None:
    if not raw:
        if region_hint and region_hint.upper() in _REGION_DEFAULT_CURRENCY:
            return _REGION_DEFAULT_CURRENCY[region_hint.upper()]
        return None
    text = raw.strip()
    if len(text) == 3 and text.isalpha():
        return text.upper()
    for sym, code in _SYMBOL_TO_ISO.items():
        if sym in text:
            return code
    if region_hint and region_hint.upper() in _REGION_DEFAULT_CURRENCY:
        return _REGION_DEFAULT_CURRENCY[region_hint.upper()]
    return None


def parse_price(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    text = re.sub(r"[^\d.,\-]", "", str(raw))
    if not text:
        return None

    has_comma = "," in text
    has_dot = "." in text
    if has_comma and has_dot:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma:
        if re.search(r",\d{1,2}$", text):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    if value < _PRICE_MIN_D or value > _PRICE_MAX_D:
        return None
    return value.quantize(Decimal("0.01"))


def parse_stock(raw: str | None) -> bool | None:
    if raw is None:
        return None
    token = raw.strip().lower()
    if not token:
        return None
    if token.startswith("http"):
        token = token.rsplit("/", 1)[-1]
    if any(t in token for t in _OUT_OF_STOCK_TOKENS):
        return False
    if any(t in token for t in _IN_STOCK_TOKENS):
        return True
    return None
