from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def register_cors_middleware(app: FastAPI, allowed_origins: list[str]) -> None:
    if not allowed_origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
