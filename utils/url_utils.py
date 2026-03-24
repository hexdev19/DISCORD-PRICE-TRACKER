from __future__ import annotations

from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
	parsed = urlparse(url)
	return parsed.scheme in {"http", "https"} and parsed.netloc.strip() != ""


def extract_domain(url: str) -> str:
	if not is_valid_url(url):
		raise ValueError("URL must include a valid domain")

	parsed = urlparse(url)
	host = parsed.netloc.lower().strip()
	if host.startswith("www."):
		host = host[4:]
	return host
