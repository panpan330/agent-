from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.routers import chat, health


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
