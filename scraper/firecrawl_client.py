from __future__ import annotations

import asyncio
import time
from typing import Any

from firecrawl import FirecrawlApp

from scraper.schemas import ProductExtractionSchema
from utils.logger import get_logger


logger = get_logger(__name__)


class FirecrawlError(Exception):
	def __init__(self, url: str, reason: str) -> None:
		super().__init__(f"Firecrawl extraction failed for '{url}': {reason}")
		self.url = url
		self.reason = reason


class FirecrawlClient:
	def __init__(self, api_key: str) -> None:
		self._app = FirecrawlApp(api_key=api_key)
		self._base_url = self._app.api_url.rstrip("/")

	async def extract(self, url: str) -> dict[str, Any]:
		results = await self.extract_many([url])
		if len(results) != 1:
			raise FirecrawlError(url, "extract did not return exactly one result")
		return results[0]

	async def extract_many(self, urls: list[str]) -> list[dict[str, Any]]:
		if not urls:
			raise FirecrawlError("", "at least one url is required")

		url_key = urls[0] if len(urls) == 1 else ",".join(urls)
		logger.info("scraper.extract_started", url=url_key)

		endpoint = f"{self._base_url}/v2/extract"
		headers = self._app._prepare_headers()
		payload = {
			"urls": urls,
			"schema": ProductExtractionSchema.model_json_schema(),
			"prompt": (
				"Extract product title, current price, currency, stock status, "
				"store name and product image URL"
			),
		}

		try:
			response = await asyncio.to_thread(self._app._post_request, endpoint, payload, headers)
			if response.status_code != 200:
				raise FirecrawlError(url_key, f"extract request returned status {response.status_code}")

			response_body = response.json()
			job_id = response_body.get("id")
			if not isinstance(job_id, str) or job_id.strip() == "":
				raise FirecrawlError(url_key, "extract response missing job id")

			data = await self._poll_extract_result(job_id=job_id, url_key=url_key, headers=headers)
			if isinstance(data, dict):
				return [data]

			if isinstance(data, list) and all(isinstance(item, dict) for item in data):
				return data

			raise FirecrawlError(url_key, "extract data payload has unsupported shape")
		except FirecrawlError:
			logger.error("scraper.extract_failed", url=url_key, exc_info=True)
			raise
		except Exception as exc:
			logger.error("scraper.extract_failed", url=url_key, exc_info=True)
			raise FirecrawlError(url_key, str(exc)) from exc

	async def _poll_extract_result(self, job_id: str, url_key: str, headers: dict[str, str]) -> Any:
		start = time.monotonic()
		while time.monotonic() - start < 60:
			status_response = await asyncio.to_thread(
				self._app._get_request,
				f"{self._base_url}/v2/extract/{job_id}",
				headers,
			)
			if status_response.status_code != 200:
				raise FirecrawlError(
					url_key,
					f"extract status request returned status {status_response.status_code}",
				)

			status_body = status_response.json()
			status = status_body.get("status")
			if status == "completed":
				if "data" not in status_body:
					raise FirecrawlError(url_key, "completed extract response missing data")

				logger.info("scraper.extract_completed", url=url_key)
				return status_body["data"]

			if status in {"failed", "cancelled"}:
				raise FirecrawlError(url_key, f"extract job ended with status '{status}'")

			await asyncio.sleep(2)

		raise FirecrawlError(url_key, "extract request timed out after 60 seconds")
