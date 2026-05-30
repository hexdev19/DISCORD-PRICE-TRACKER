from __future__ import annotations

import secrets
from typing import Any

import httpx
from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import security
from app.api.deps import current_user, db_session
from app.config.settings import get_settings
from app.models.user import User
from app.services import discord_oauth
from app.services.user_service import UserService
from app.utils.logger import get_logger

log = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/discord/login")
async def discord_login() -> RedirectResponse:
    nonce = secrets.token_urlsafe(16)
    response = RedirectResponse(discord_oauth.login_url(nonce))
    security.set_state_cookie(response, security.issue_state(nonce))
    return response


@router.get("/discord/callback")
async def discord_callback(
    session: AsyncSession = Depends(db_session),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: str | None = Cookie(default=None, alias=security.STATE_COOKIE),
) -> RedirectResponse:
    dashboard = get_settings().dashboard_url
    if error:
        return RedirectResponse(f"{dashboard}/?auth=cancelled")
    if not code or not security.check_state(oauth_state, state):
        return RedirectResponse(f"{dashboard}/?auth=error")
    try:
        profile = await discord_oauth.fetch_profile(code)
    except httpx.HTTPError:
        log.warning("oauth.exchange_failed")
        return RedirectResponse(f"{dashboard}/?auth=error")

    user = await UserService(session).upsert_from_discord(
        discord_id=profile.id,
        discord_username=profile.username,
        discord_avatar=profile.avatar,
        email=profile.email,
    )
    response = RedirectResponse(f"{dashboard}/dashboard")
    security.set_session_cookie(response, security.create_session(str(user.id)))
    security.clear_state_cookie(response)
    return response


@router.get("/discord/bot")
async def discord_bot() -> RedirectResponse:
    nonce = secrets.token_urlsafe(16)
    response = RedirectResponse(discord_oauth.bot_url(nonce))
    security.set_state_cookie(response, security.issue_state(nonce))
    return response


@router.get("/discord/bot/callback")
async def discord_bot_callback(
    state: str | None = None,
    guild_id: str | None = None,
    error: str | None = None,
    oauth_state: str | None = Cookie(default=None, alias=security.STATE_COOKIE),
) -> RedirectResponse:
    dashboard = get_settings().dashboard_url
    if error:
        return RedirectResponse(f"{dashboard}/?bot=cancelled")
    if not guild_id or not security.check_state(oauth_state, state):
        return RedirectResponse(f"{dashboard}/?bot=error")
    log.info("bot.authorized", guild_id=guild_id)
    response = RedirectResponse(f"{dashboard}/dashboard?bot=added")
    security.clear_state_cookie(response)
    return response


@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "discordId": str(user.discord_id),
        "username": user.discord_username,
        "avatar": user.discord_avatar,
        "email": user.email,
        "plan": user.plan,
    }


@router.post("/logout")
async def logout() -> JSONResponse:
    response = JSONResponse({"ok": True})
    security.clear_session_cookie(response)
    return response
