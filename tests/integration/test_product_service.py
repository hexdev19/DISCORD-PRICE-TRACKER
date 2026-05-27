from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.errors import InvalidInput
from app.services.product_service import ProductService

pytestmark = pytest.mark.integration


async def test_canonicalizes_and_dedupes(session: AsyncSession) -> None:
    svc = ProductService(session)
    p1, created1 = await svc.find_or_create_by_url(
        "https://Example.com/p/1?utm_source=ads&id=42"
    )
    await session.commit()
    assert created1 is True
    assert p1.source_url == "https://example.com/p/1?id=42"
    assert p1.domain == "example.com"

    p2, created2 = await svc.find_or_create_by_url("https://example.com/p/1?id=42&fbclid=x")
    await session.commit()
    assert created2 is False
    assert p2.id == p1.id


async def test_rejects_unsafe_url(session: AsyncSession) -> None:
    svc = ProductService(session)
    with pytest.raises(InvalidInput):
        await svc.find_or_create_by_url("ftp://example.com/file")
