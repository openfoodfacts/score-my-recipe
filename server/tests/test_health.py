from fastapi.testclient import TestClient

from api.api import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    response = client.get("/v1/health")
    data = response.json()
    assert data["status"] == "ok"
    assert "ecobalyse" in data
