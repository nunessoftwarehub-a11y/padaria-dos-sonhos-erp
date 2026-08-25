"""Focused regression tests for password recovery and login lockout."""
import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def test_forgot_password_accepts_email_only():
    response = requests.post(
        f"{BASE_URL}/api/auth/forgot-password",
        json={"email": f"TEST_{uuid.uuid4().hex}@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["message"]


def test_login_locks_after_five_failures():
    email = f"TEST_{uuid.uuid4().hex}@example.com"
    password = "padaria123"
    register = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"name": "Lockout Test", "email": email, "password": password},
    )
    assert register.status_code == 200
    session = requests.Session()
    failures = [
        session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": "wrongpass"},
        ).status_code
        for _ in range(5)
    ]
    assert failures == [401, 401, 401, 401, 401]
    locked = session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
    )
    assert locked.status_code == 429