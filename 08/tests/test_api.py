from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    model_path = Path(__file__).resolve().parents[1] / "model" / "iris_rules.json"
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_success(client: TestClient) -> None:
    payload = {"features": [5.1, 3.5, 1.4, 0.2], "request_id": "req-1"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v1"
    assert data["request_id"] == "req-1"
    assert data["prediction"] == "setosa"
    assert data["confidence"] == 1.0


def test_predict_invalid_length(client: TestClient) -> None:
    response = client.post("/predict", json={"features": [1.0]})
    assert response.status_code == 422
    assert "Expected 4 features" in response.json()["detail"]


def test_predict_invalid_payload(client: TestClient) -> None:
    response = client.post("/predict", json={})
    assert response.status_code == 422
