from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from app.config.settings import get_settings

_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
_TOKEN_URL = "https://discord.com/api/oauth2/token"
_USER_URL = "https://discord.com/api/users/@me"
_LOGIN_SCOPES = "identify email"
_BOT_SCOPES = "bot applications.commands"


@dataclass(frozen=True)
class DiscordProfile:
    id: int
    username: str
    avatar: str | None
    email: str | None


def _login_redirect_uri() -> str:
    return f"{get_settings().api_public_url}/auth/discord/callback"


def _bot_redirect_uri() -> str:
    return f"{get_settings().api_public_url}/auth/discord/bot/callback"


def login_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": _login_redirect_uri(),
        "response_type": "code",
        "scope": _LOGIN_SCOPES,
        "state": state,
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


def bot_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.discord_client_id,
        "redirect_uri": _bot_redirect_uri(),
        "response_type": "code",
        "scope": _BOT_SCOPES,
        "permissions": settings.discord_bot_permissions,
        "state": state,
    }
    return f"{_AUTHORIZE_URL}?{urlencode(params)}"


async def fetch_profile(code: str) -> DiscordProfile:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            _TOKEN_URL,
            data={
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _login_redirect_uri(),
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        user_resp = await client.get(_USER_URL, headers={"Authorization": f"Bearer {access_token}"})
        user_resp.raise_for_status()
        user = user_resp.json()

    return DiscordProfile(
        id=int(user["id"]),
        username=user.get("global_name") or user.get("username") or "",
        avatar=user.get("avatar"),
        email=user.get("email"),
    )
