"""Adapter package — import side-effect registers each adapter."""

from __future__ import annotations

from app.scraper.adapters import (  # noqa: F401
    aliexpress,
    amazon,
    bestbuy,
    ebay,
    target,
    walmart,
)
from app.scraper.adapters.base import (
    SiteAdapter,
    find_adapter,
    registered_adapters,
)

__all__ = ["SiteAdapter", "find_adapter", "registered_adapters"]
