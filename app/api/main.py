from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routers import auth, dashboard
from app.config.settings import get_settings
from app.observability.logging import configure_logging
from app.observability.sentry import init_sentry
from app.observability.tracing import init_tracing


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_sentry("api")
    init_tracing("api")

    app = FastAPI(title="Price Tracker API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.dashboard_url],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    register_error_handlers(app)

    if settings.otel_exporter_otlp_endpoint:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
