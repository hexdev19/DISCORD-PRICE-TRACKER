"""Tier 4 — Scrapling ``AsyncStealthySession`` wrapper.

One persistent session per worker process; ``max_pages`` from limits.py.
Importing this module does not start a browser — the session is started
lazily on first ``render`` call.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.config.limits import BROWSER_MAX_PAGES, BROWSER_NAV_TIMEOUT_SECONDS
from app.utils.url_utils import resolve_url_safely


class BrowserSession:
    def __init__(self) -> None:
        self._session: Any | None = None
        self._lock = asyncio.Lock()

    async def render(self, url: str) -> str | None:
        resolve_url_safely(url)
        session = await self._ensure_session()
        page = await session.fetch(
            url,
            timeout=BROWSER_NAV_TIMEOUT_SECONDS * 1000,
        )
        body = getattr(page, "body", None) or getattr(page, "html_content", None)
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")
        return body

    async def close(self) -> None:
        async with self._lock:
            if self._session is None:
                return
            close = getattr(self._session, "close", None)
            if close is not None:
                await close()
            self._session = None

    async def _ensure_session(self) -> Any:
        if self._session is not None:
            return self._session
        async with self._lock:
            if self._session is not None:
                return self._session
            from scrapling.fetchers import AsyncStealthySession  # type: ignore[import-not-found]

            self._session = AsyncStealthySession(
                headless=True,
                max_pages=BROWSER_MAX_PAGES,
                solve_cloudflare=True,
                disable_resources=True,
            )
            start = getattr(self._session, "__aenter__", None)
            if start is not None:
                await start()
            return self._session


_singleton: BrowserSession | None = None


def get_browser_session() -> BrowserSession:
    global _singleton
    if _singleton is None:
        _singleton = BrowserSession()
    return _singleton


async def shutdown_browser_session() -> None:
    global _singleton
    if _singleton is not None:
        await _singleton.close()
        _singleton = None
