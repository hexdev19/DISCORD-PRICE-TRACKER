from __future__ import annotations

from urllib.parse import urlparse


def extract_domain(url: str) -> str:
	parsed = urlparse(url)
	host = parsed.netloc.lower().strip()
	if host.startswith("www."):
		host = host[4:]
	if host == "":
		raise ValueError("URL must include a valid domain")
	return host
