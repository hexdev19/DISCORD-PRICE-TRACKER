from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest

from scraper.schemas import ScrapedProduct
from scraper.scrape_service import ScrapeError, ScrapeService


class _ClientSuccess:
    async def extract(self, url: str) -> dict:
        return {"title": "Phone", "source": url}

    async def extract_many(self, urls: list[str]) -> list[dict]:
        return [{"title": f"Product-{index}", "source": value} for index, value in enumerate(urls)]


class _ClientFail:
    async def extract(self, url: str) -> dict:
        raise RuntimeError("network failure")

    async def extract_many(self, urls: list[str]) -> list[dict]:
        raise RuntimeError("network failure")


class _ExtractorSuccess:
    def extract(self, data: dict, source_url: str) -> ScrapedProduct:
        return ScrapedProduct(
            title=str(data["title"]),
            price=Decimal("10.00"),
            currency="USD",
            in_stock=True,
            image_url=None,
            store_name="Test Store",
            source_url=source_url,
        )


class _ExtractorFail:
    def extract(self, data: dict, source_url: str) -> ScrapedProduct:
        raise ValueError("bad extraction")



def test_scrape_returns_scraped_product() -> None:
    service = ScrapeService(client=_ClientSuccess(), extractor=_ExtractorSuccess())

    result = asyncio.run(service.scrape("https://example.com/p/1"))

    assert result.title == "Phone"
    assert result.source_url == "https://example.com/p/1"



def test_scrape_wraps_client_error() -> None:
    service = ScrapeService(client=_ClientFail(), extractor=_ExtractorSuccess())

    with pytest.raises(ScrapeError):
        asyncio.run(service.scrape("https://example.com/p/1"))



def test_scrape_wraps_extractor_error() -> None:
    service = ScrapeService(client=_ClientSuccess(), extractor=_ExtractorFail())

    with pytest.raises(ScrapeError):
        asyncio.run(service.scrape("https://example.com/p/1"))



def test_scrape_many_returns_scraped_products() -> None:
    service = ScrapeService(client=_ClientSuccess(), extractor=_ExtractorSuccess())

    urls = ["https://example.com/p/1", "https://example.com/p/2"]
    result = asyncio.run(service.scrape_many(urls))

    assert len(result) == 2
    assert result[0].source_url == "https://example.com/p/1"
    assert result[1].source_url == "https://example.com/p/2"



def test_scrape_many_wraps_client_error() -> None:
    service = ScrapeService(client=_ClientFail(), extractor=_ExtractorSuccess())

    with pytest.raises(ScrapeError):
        asyncio.run(service.scrape_many(["https://example.com/p/1", "https://example.com/p/2"]))



def test_scrape_many_wraps_mismatched_result_count() -> None:
    class _ClientMismatch:
        async def extract(self, url: str) -> dict:
            return {"title": "Phone", "source": url}

        async def extract_many(self, urls: list[str]) -> list[dict]:
            return [{"title": "Only one", "source": urls[0]}]

    service = ScrapeService(client=_ClientMismatch(), extractor=_ExtractorSuccess())

    with pytest.raises(ScrapeError):
        asyncio.run(service.scrape_many(["https://example.com/p/1", "https://example.com/p/2"]))
