from pathlib import Path
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import create_app  # noqa: E402
from app.services.ticket_service import clear_ticket_store  # noqa: E402


@pytest.fixture(autouse=True)
def clear_tickets() -> None:
    clear_ticket_store()
    yield
    clear_ticket_store()


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
