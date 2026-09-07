import pytest
from starlette.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_recommendations_get_endpoint_structure(client: TestClient):
    """Test GET /api/v1/recommendations returns 200 with list of destinations."""
    response = client.get("/api/v1/recommendations?limit=3&query=beach")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "name" in item
        assert "country" in item
        assert "id" in item
        assert "slug" in item


def test_recommendations_post_endpoint(client: TestClient):
    """Test POST /api/v1/recommendations with rich JSON payload."""
    payload = {
        "prompt": "I want an adventurous mountain trekking experience with scenic landscapes",
        "preferences": ["hiking", "mountains", "photography"],
        "travel_style": "Adventure",
        "budget_level": "Mid-range",
        "limit": 3
    }
    response = client.post("/api/v1/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3
    if len(data) > 0:
        item = data[0]
        assert "name" in item
        assert "country" in item
        assert "recommendation_reason" in item
        assert item.get("recommendation_reason") is not None
        assert "match_score" in item
        assert item.get("match_score") is not None
        print(f"Generated destination: {item['name']} ({item['country']}) - Reason: {item['recommendation_reason']}")


def test_recommendations_fallback_resilience(client: TestClient, monkeypatch):
    """Test recommendation engine fallback when Gemini key is empty."""
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    response = client.get("/api/v1/recommendations?query=culture&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
