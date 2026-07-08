from fastapi import FastAPI

from app.core.config import get_settings
from app.core.cors import register_cors_middleware
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.tracing import register_trace_middleware
from app.routers import chat, health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )
    register_exception_handlers(app)
    register_trace_middleware(app)
    register_cors_middleware(app, settings.cors_allowed_origin_list)
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
