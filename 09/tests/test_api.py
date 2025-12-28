from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    model_path = Path(__file__).resolve().parents[1] / "model" / "iris_rules.json"
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-pass")
    monkeypatch.setenv("USER_USERNAME", "user")
    monkeypatch.setenv("USER_PASSWORD", "user-pass")
    with TestClient(app) as test_client:
        yield test_client


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_invalid(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json={"username": "user", "password": "bad"},
    )
    assert response.status_code == 401


def test_predict_requires_auth(client: TestClient) -> None:
    response = client.post("/predict", json={"features": [5.1, 3.5, 1.4, 0.2]})
    assert response.status_code == 403


def test_predict_success(client: TestClient) -> None:
    token = _login(client, "user", "user-pass")
    payload = {"features": [5.1, 3.5, 1.4, 0.2], "request_id": "req-1"}
    response = client.post(
        "/predict",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_version"] == "v1"
    assert data["request_id"] == "req-1"
    assert data["prediction"] == "setosa"
    assert data["confidence"] == 1.0


def test_predict_invalid_length(client: TestClient) -> None:
    token = _login(client, "user", "user-pass")
    response = client.post(
        "/predict",
        json={"features": [1.0]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "Expected 4 features" in response.json()["detail"]


def test_predict_invalid_payload(client: TestClient) -> None:
    token = _login(client, "user", "user-pass")
    response = client.post(
        "/predict",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_admin_reload_forbidden(client: TestClient) -> None:
    token = _login(client, "user", "user-pass")
    response = client.post(
        "/admin/reload",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_reload_success(client: TestClient) -> None:
    token = _login(client, "admin", "admin-pass")
    response = client.post(
        "/admin/reload",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "reloaded"
