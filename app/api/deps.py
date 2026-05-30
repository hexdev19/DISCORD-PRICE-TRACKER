from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security import SESSION_COOKIE, read_session
from app.db.session import SessionFactory
from app.models.user import User
from app.repositories.user_repo import UserRepository


async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def current_user(
    session: AsyncSession = Depends(db_session),
    session_cookie: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    user_id = read_session(session_cookie)
    if user_id is not None:
        try:
            user = await UserRepository(session).get(uuid.UUID(user_id))
        except ValueError:
            user = None
        if user is not None and user.deleted_at is None:
            return user
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
