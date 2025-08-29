import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_stats_empty(client: TestClient):
    """Test stats endpoint with no data."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["images"] == 0
    assert data["duplicates"] == 0
    assert data["rounds"] == 0
    assert data["by_image"] == []


def test_get_pair_no_images(client: TestClient):
    """Test pair endpoint with no images."""
    response = client.get("/api/pair")
    assert response.status_code == 404
    assert "Not enough images" in response.json()["detail"]


def test_submit_choice_invalid_selection(client: TestClient):
    """Test choice endpoint with invalid selection."""
    response = client.post("/api/choice", json={
        "round": 1,
        "left_id": "test-id-1",
        "right_id": "test-id-2",
        "selection": "INVALID"
    })
    assert response.status_code == 400
    assert "Selection must be" in response.json()["detail"]