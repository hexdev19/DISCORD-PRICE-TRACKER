"""Minimal Discord REST client for alert delivery.

POSTs an embed to ``/channels/{id}/messages``. Returns a discriminated
``DispatchOutcome`` so the calling task can decide retry vs permanent
failure without parsing exceptions. 429 is honored via ``Retry-After``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.config.settings import get_settings
from app.utils.logger import get_logger

log = get_logger(__name__)

DispatchStatus = Literal[
    "delivered",
    "rate_limited",
    "channel_gone",
    "permission_denied",
    "server_error",
    "network_error",
]


@dataclass(frozen=True, slots=True)
class DispatchOutcome:
    status: DispatchStatus
    retry_after: float | None = None
    detail: str | None = None


class DiscordDispatcher:
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._token = get_settings().discord_token

    async def send_message(
        self,
        *,
        channel_id: int,
        embed: dict[str, Any],
        content: str | None = None,
    ) -> DispatchOutcome:
        payload: dict[str, Any] = {"embeds": [embed]}
        if content:
            payload["content"] = content

        try:
            client = self._client or httpx.AsyncClient(timeout=10.0)
            owns_client = self._client is None
            try:
                response = await client.post(
                    f"https://discord.com/api/v10/channels/{channel_id}/messages",
                    headers={
                        "Authorization": f"Bot {self._token}",
                        "User-Agent": "price-tracker (https://example.com, 0.1.0)",
                    },
                    json=payload,
                )
            finally:
                if owns_client:
                    await client.aclose()
        except httpx.RequestError as exc:
            log.warning("dispatch.network_error", error=type(exc).__name__)
            return DispatchOutcome(status="network_error", detail=type(exc).__name__)

        status = response.status_code
        if 200 <= status < 300:
            return DispatchOutcome(status="delivered")
        if status == 429:
            retry_after = _parse_retry_after(response)
            return DispatchOutcome(status="rate_limited", retry_after=retry_after)
        if status in (403,):
            return DispatchOutcome(status="permission_denied", detail=response.text[:200])
        if status in (404,):
            return DispatchOutcome(status="channel_gone", detail=response.text[:200])
        return DispatchOutcome(status="server_error", detail=f"http {status}")


def _parse_retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if raw is None:
        try:
            data = response.json()
        except ValueError:
            return None
        return float(data.get("retry_after")) if "retry_after" in data else None
    try:
        return float(raw)
    except ValueError:
        return None
