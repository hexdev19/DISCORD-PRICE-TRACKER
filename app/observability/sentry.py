from __future__ import annotations

import sentry_sdk

from app.config.settings import get_settings


def init_sentry(service: str) -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=settings.release_sha,
        send_default_pii=False,
        traces_sample_rate=0.0,
    )
    sentry_sdk.set_tag("service", service)
