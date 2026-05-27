from __future__ import annotations

from typing import Any

from app.config.limits import RESPONSE_SIZE_CAP_BYTES
from app.utils.url_utils import resolve_url_safely


class FetchError(RuntimeError):
    pass


async def fetch_html(url: str) -> str:
    resolve_url_safely(url)
    from scrapling.fetchers import AsyncFetcher  # type: ignore[import-not-found]

    fetcher = AsyncFetcher()
    response: Any = await fetcher.get(url, stealthy_headers=True, timeout=15)
    status = int(getattr(response, "status", 0) or 0)
    if status >= 400:
        raise FetchError(f"http {status}")

    body = getattr(response, "body", None) or getattr(response, "html_content", None) or ""
    if isinstance(body, bytes):
        if len(body) > RESPONSE_SIZE_CAP_BYTES:
            raise FetchError("response exceeds size cap")
        return body.decode("utf-8", errors="replace")
    if len(body) > RESPONSE_SIZE_CAP_BYTES:
        raise FetchError("response exceeds size cap")
    return body
