import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_health_probe_returns_200(client: TestClient):
    """Verify /health probe returns HTTP 200 with status 'ok' and service map."""
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got: {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("version") == settings.VERSION
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]


def test_api_v1_root_returns_200(client: TestClient):
    """Verify /api/v1 returns HTTP 200 with welcome message and active status."""
    response = client.get("/api/v1")
    assert response.status_code == 200, f"Expected 200, got: {response.status_code}"
    data = response.json()
    assert data.get("message") == "Welcome to the AI Tourism API v1"
    assert data.get("status") == "active"


def test_api_v1_health_returns_200(client: TestClient):
    """Verify /api/v1/health returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200, f"Expected 200, got: {response.status_code}"
    data = response.json()
    assert data.get("status") == "ok"


def test_health_post_not_allowed(client: TestClient):
    """Verify POST /health returns 405 Method Not Allowed."""
    response = client.post("/health", json={"test": "data"})
    assert response.status_code == 405


def test_nonexistent_route_returns_404(client: TestClient):
    """Verify requesting an undefined route returns 404."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404


def test_app_metadata():
    """Verify FastAPI application title and version match configuration."""
    assert app.title == settings.PROJECT_NAME
    assert app.version == settings.VERSION
