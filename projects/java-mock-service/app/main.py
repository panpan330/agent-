from fastapi import FastAPI

from app.core.exception_handlers import register_exception_handlers
from app.routers import health, orders


def create_app() -> FastAPI:
    app = FastAPI(
        title="Java Mock Business Service",
        description="A small FastAPI service that simulates a Java order service.",
        version="0.1.0",
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(orders.router)
    return app


app = create_app()
