from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings


engine = create_async_engine(
	settings.POSTGRES_URL,
	pool_pre_ping=True,
	echo=False,
)

AsyncSessionFactory = async_sessionmaker(
	bind=engine,
	expire_on_commit=False,
	class_=AsyncSession,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
	async with AsyncSessionFactory() as session:
		yield session
