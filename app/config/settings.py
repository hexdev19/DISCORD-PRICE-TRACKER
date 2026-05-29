from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["dev", "test", "staging", "prod"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: AppEnv = "dev"
    log_level: str = "INFO"

    database_url: str
    redis_url: str

    discord_token: str
    discord_client_id: str
    discord_client_secret: str

    session_cookie_secret: str = Field(min_length=32)
    oauth_token_enc_key: str = Field(min_length=32)

    sentry_dsn: str | None = None
    otel_exporter_otlp_endpoint: str | None = None
    release_sha: str | None = None

    proxy_url: str | None = None

    firecrawl_api_key: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
