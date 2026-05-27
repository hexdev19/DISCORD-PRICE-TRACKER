from __future__ import annotations

import httpx
import pytest

from app.workers.discord_dispatcher import DiscordDispatcher


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_204_treated_as_delivered() -> None:
    async def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    async with _client(handler) as client:
        outcome = await DiscordDispatcher(client=client).send_message(
            channel_id=1, embed={"title": "t"}
        )
    assert outcome.status == "delivered"


async def test_rate_limited_parses_retry_after_header() -> None:
    async def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "1.5"}, json={})

    async with _client(handler) as client:
        outcome = await DiscordDispatcher(client=client).send_message(
            channel_id=1, embed={"title": "t"}
        )
    assert outcome.status == "rate_limited"
    assert outcome.retry_after == pytest.approx(1.5)


async def test_403_is_permission_denied() -> None:
    async def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="no")

    async with _client(handler) as client:
        outcome = await DiscordDispatcher(client=client).send_message(
            channel_id=1, embed={"title": "t"}
        )
    assert outcome.status == "permission_denied"


async def test_404_is_channel_gone() -> None:
    async def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="no")

    async with _client(handler) as client:
        outcome = await DiscordDispatcher(client=client).send_message(
            channel_id=1, embed={"title": "t"}
        )
    assert outcome.status == "channel_gone"


async def test_network_error_returns_outcome() -> None:
    async def handler(_req: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    async with _client(handler) as client:
        outcome = await DiscordDispatcher(client=client).send_message(
            channel_id=1, embed={"title": "t"}
        )
    assert outcome.status == "network_error"
