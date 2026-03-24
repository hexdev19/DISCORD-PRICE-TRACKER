from __future__ import annotations

from itertools import zip_longest

from config.settings import Settings
from scraper.extractor import ProductExtractor
from scraper.firecrawl_client import FirecrawlClient
from scraper.schemas import ScrapedProduct
from utils.logger import get_logger


logger = get_logger(__name__)


class ScrapeError(Exception):
	def __init__(self, url: str) -> None:
		super().__init__(f"Failed to scrape URL: {url}")
		self.url = url


class ScrapeService:
	def __init__(self, client: FirecrawlClient, extractor: ProductExtractor) -> None:
		self._client = client
		self._extractor = extractor

	async def scrape(self, url: str) -> ScrapedProduct:
		logger.info("scrape.started", url=url)
		try:
			raw_data = await self._client.extract(url)
			product = self._extractor.extract(raw_data, url)
		except Exception as exc:
			raise ScrapeError(url) from exc

		logger.info("scrape.completed", url=url, title=product.title)
		return product

	async def scrape_many(self, urls: list[str]) -> list[ScrapedProduct]:
		if not urls:
			raise ScrapeError("")

		url_key = urls[0] if len(urls) == 1 else ",".join(urls)
		logger.info("scrape.started", url=url_key)

		try:
			raw_data = await self._client.extract_many(urls)
			products: list[ScrapedProduct] = []
			for source_url, item in zip_longest(urls, raw_data):
				if source_url is None or item is None:
					raise ScrapeError(url_key)
				products.append(self._extractor.extract(item, source_url))
		except Exception as exc:
			raise ScrapeError(url_key) from exc

		logger.info("scrape.completed", url=url_key, title=products[0].title)
		return products


def build_scrape_service(settings: Settings) -> ScrapeService:
	client = FirecrawlClient(api_key=settings.FIRECRAWL_API_KEY)
	extractor = ProductExtractor()
	return ScrapeService(client=client, extractor=extractor)
