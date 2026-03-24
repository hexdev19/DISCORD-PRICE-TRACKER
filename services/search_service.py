from __future__ import annotations

import httpx

from config.settings import settings
from services import AppError
from utils.logger import get_logger


logger = get_logger(__name__)


class SearchError(AppError):
	pass


class SearchService:
	async def search_urls(self, query: str, location: str | None) -> list[str]:
		payload = {"q": query }
		if location and location.strip():
			payload["gl"] = location.strip().lower()
		page_two_payload = dict(payload)
		page_two_payload["page"] = 2
		headers = {
			"X-API-KEY": settings.SERPER_API_KEY,
			"Content-Type": "application/json",
		}

		logger.info("search.search_urls.started", query=query, location=location)
		try:
			async with httpx.AsyncClient(timeout=15.0) as client:
				response_page_one = await client.post("https://google.serper.dev/search", headers=headers, json=payload)
				response_page_one.raise_for_status()
				response_page_two = await client.post(
					"https://google.serper.dev/search",
					headers=headers,
					json=page_two_payload,
				)
				response_page_two.raise_for_status()
		except httpx.HTTPError as exc:
			raise SearchError("Serper API request failed") from exc

		data_page_one = response_page_one.json()
		data_page_two = response_page_two.json()
		organic_page_one = data_page_one.get("organic", [])
		organic_page_two = data_page_two.get("organic", [])
		links_page_one = [
			row.get("link", "")
			for row in organic_page_one
			if isinstance(row, dict) and row.get("link")
		]
		links_page_two = [
			row.get("link", "")
			for row in organic_page_two
			if isinstance(row, dict) and row.get("link")
		]
		links = list(dict.fromkeys([*links_page_one, *links_page_two]))
		if not links:
			raise SearchError("No search results found")

		logger.info("search.search_urls.completed", query=query, location=location, results=len(links))
		return links
