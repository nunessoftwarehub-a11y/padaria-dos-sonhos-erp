"""Regression coverage for health, authentication, session and dashboard APIs."""
import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture
def client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


def test_backend_url_configured():
    assert BASE_URL, "REACT_APP_BACKEND_URL is required"


def test_api_health(client):
    response = client.get(f"{BASE_URL}/api/")
    assert response.status_code == 200
    assert response.json() == {"service": "Padaria dos Sonhos ERP", "status": "online"}


def test_register_sets_http_only_session_and_dashboard(client):
    email = f"TEST_{uuid.uuid4().hex}@example.com"
    response = client.post(
        f"{BASE_URL}/api/auth/register",
        json={"name": "Ana Sonhos", "email": email, "password": "padaria123"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user["email"] == email.lower()
    assert user["role"] == "staff"
    assert "password_hash" not in user
    cookie = response.cookies.get_dict().get("access_token")
    assert cookie
    assert "access_token" in response.headers.get("set-cookie", "")
    assert "HttpOnly" in response.headers.get("set-cookie", "")

    me = client.get(f"{BASE_URL}/api/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]

    dashboard = client.get(f"{BASE_URL}/api/dashboard")
    assert dashboard.status_code == 200
    data = dashboard.json()
    # Dashboard starts empty: no demonstrative metrics, sales or inventory.
    assert data["metrics"] == []
    assert data["sales"] == []
    assert data["inventory"] == []

    logout = client.post(f"{BASE_URL}/api/auth/logout", json={})
    assert logout.status_code == 200
    assert client.get(f"{BASE_URL}/api/auth/me").status_code == 401


def test_login_and_duplicate_registration(client):
    email = f"TEST_{uuid.uuid4().hex}@example.com"
    payload = {"name": "Teste Login", "email": email, "password": "padaria123"}
    assert client.post(f"{BASE_URL}/api/auth/register", json=payload).status_code == 200
    login = client.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": payload["password"]})
    assert login.status_code == 200
    assert login.json()["email"] == email.lower()
    bad = client.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "wrongpass"})
    assert bad.status_code == 401
    duplicate = client.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert duplicate.status_code == 409


def test_protected_dashboard_rejects_anonymous(client):
    response = client.get(f"{BASE_URL}/api/dashboard")
    assert response.status_code == 401


def test_cors_allows_credentials_for_frontend_origin(client):
    origin = BASE_URL
    response = client.options(
        f"{BASE_URL}/api/auth/me",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert response.headers.get("access-control-allow-origin") == origin