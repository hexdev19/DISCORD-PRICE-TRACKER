from __future__ import annotations

import re

_ASIN_RE = re.compile(r"/(?:dp|gp/product|gp/aw/d)/([A-Z0-9]{10})(?:[/?]|$)")
_EBAY_ITEM_RE = re.compile(r"/itm/(?:[\w-]+/)?(\d{9,14})")


def from_url(url: str) -> dict[str, str]:
    out: dict[str, str] = {}
    asin = _ASIN_RE.search(url)
    if asin:
        out["asin"] = asin.group(1)
    ebay = _EBAY_ITEM_RE.search(url)
    if ebay:
        out["mpn"] = ebay.group(1)
    return out
