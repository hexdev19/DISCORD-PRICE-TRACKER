from __future__ import annotations

from pydantic import ValidationError

from scraper.schemas import ProductExtractionSchema, ScrapedProduct
from utils.logger import get_logger


logger = get_logger(__name__)


class ExtractionError(Exception):
	pass


class ProductExtractor:
	def extract(self, data: dict, source_url: str) -> ScrapedProduct:
		try:
			extraction = ProductExtractionSchema.model_validate(data)
			scraped_product = ScrapedProduct.from_extraction(extraction, source_url)
			logger.info("extractor.parsed", source_url=source_url, title=scraped_product.title)
			return scraped_product
		except (ValidationError, ValueError) as exc:
			logger.error("extractor.failed", source_url=source_url, exc_info=True)
			raise ExtractionError(str(exc)) from exc
