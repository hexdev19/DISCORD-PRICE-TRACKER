from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Response

from app.config.settings import get_settings

SESSION_COOKIE = "session"
STATE_COOKIE = "oauth_state"
_SESSION_TTL = 60 * 60 * 24 * 14
_STATE_TTL = 60 * 10


def _secret() -> bytes:
    return get_settings().session_cookie_secret.encode()


def _secure() -> bool:
    return get_settings().app_env != "dev"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(payload: dict[str, Any]) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _verify(token: str, *, max_age: int) -> dict[str, Any] | None:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    issued = payload.get("iat")
    if not isinstance(issued, (int, float)) or time.time() - issued > max_age:
        return None
    return payload


def create_session(user_id: str) -> str:
    return _sign({"sub": user_id, "iat": int(time.time())})


def read_session(token: str | None) -> str | None:
    if not token:
        return None
    payload = _verify(token, max_age=_SESSION_TTL)
    sub = payload.get("sub") if payload else None
    return sub if isinstance(sub, str) else None


def issue_state(nonce: str) -> str:
    return _sign({"n": nonce, "iat": int(time.time())})


def check_state(cookie: str | None, state_param: str | None) -> bool:
    if not cookie or not state_param:
        return False
    payload = _verify(cookie, max_age=_STATE_TTL)
    if payload is None:
        return False
    return hmac.compare_digest(str(payload.get("n", "")), state_param)


def set_session_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        value,
        max_age=_SESSION_TTL,
        httponly=True,
        secure=_secure(),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax", secure=_secure())


def set_state_cookie(response: Response, value: str) -> None:
    response.set_cookie(
        STATE_COOKIE,
        value,
        max_age=_STATE_TTL,
        httponly=True,
        secure=_secure(),
        samesite="lax",
        path="/",
    )


def clear_state_cookie(response: Response) -> None:
    response.delete_cookie(STATE_COOKIE, path="/", samesite="lax", secure=_secure())
