from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check() -> None:
    client = TestClient(create_app())

    response = client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["service"] == "ai-service"
    assert isinstance(data["time"], str)
