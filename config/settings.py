from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)


def _read_required_env(name: str) -> str:
	value = os.getenv(name)
	if value is None or value.strip() == "":
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value


def _read_int_env(name: str, default: int) -> int:
	value = os.getenv(name)
	if value is None or value.strip() == "":
		return default
	return int(value)


@dataclass(frozen=True)
class Settings:
	DISCORD_TOKEN: str
	POSTGRES_URL: str
	REDIS_URL: str
	SERPER_API_KEY: str
	FIRECRAWL_API_KEY: str
	MONITOR_INTERVAL: int


settings = Settings(
	DISCORD_TOKEN=_read_required_env("DISCORD_TOKEN"),
	POSTGRES_URL=_read_required_env("POSTGRES_URL"),
	REDIS_URL=_read_required_env("REDIS_URL"),
	SERPER_API_KEY=_read_required_env("SERPER_API_KEY"),
	FIRECRAWL_API_KEY=_read_required_env("FIRECRAWL_API_KEY"),
	MONITOR_INTERVAL=_read_int_env("MONITOR_INTERVAL", 300),
)
