"""Iteration 9 — settings, employees/permissions, expenses, dashboard bar chart."""
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "caixa.pdv@padaria.com"
ADMIN_PASSWORD = "padaria123"
CASHIER_EMAIL = "joao.caixa@padaria.com"
CASHIER_PASSWORD = "caixa123"


def _login(email, password):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    return s, r


@pytest.fixture(scope="module")
def admin_session():
    assert BASE_URL, "REACT_APP_BACKEND_URL required"
    s, r = _login(ADMIN_EMAIL, ADMIN_PASSWORD)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["role"] == "admin"
    return s, data


@pytest.fixture(scope="module")
def cashier_session(admin_session):
    s, r = _login(CASHIER_EMAIL, CASHIER_PASSWORD)
    if r.status_code != 200:
        # Recreate the seed cashier if missing (previous tests may have deleted them)
        admin_s, _ = admin_session
        admin_s.post(
            f"{BASE_URL}/api/employees",
            json={"name": "João Caixa", "email": CASHIER_EMAIL, "password": CASHIER_PASSWORD, "role": "cashier"},
        )
        s, r = _login(CASHIER_EMAIL, CASHIER_PASSWORD)
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "cashier"
    return s, r.json()


# ---------- Settings ----------

def test_settings_get_and_update(admin_session):
    s, _ = admin_session
    r = s.get(f"{BASE_URL}/api/settings")
    assert r.status_code == 200
    original = r.json()
    assert "bakery_name" in original and "primary_color" in original

    # Update
    r = s.put(f"{BASE_URL}/api/settings", json={"bakery_name": "TEST Padaria", "primary_color": "#B91C1C"})
    assert r.status_code == 200
    updated = r.json()
    assert updated["bakery_name"] == "TEST Padaria"
    assert updated["primary_color"] == "#B91C1C"

    # Persistence
    r = s.get(f"{BASE_URL}/api/settings")
    assert r.json()["bakery_name"] == "TEST Padaria"

    # Restore
    r = s.put(
        f"{BASE_URL}/api/settings",
        json={"bakery_name": "Padaria dos Sonhos", "primary_color": "#B45309"},
    )
    assert r.status_code == 200
    assert r.json()["bakery_name"] == "Padaria dos Sonhos"


def test_settings_logo_upload_download(admin_session):
    s, _ = admin_session
    # 1x1 red PNG
    png = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6300010000000500010D0A2DB40000000049454E44AE426082"
    )
    files = {"file": ("logo.png", io.BytesIO(png), "image/png")}
    r = s.post(f"{BASE_URL}/api/settings/logo", files=files)
    assert r.status_code == 200, r.text
    assert "logo_path" in r.json()

    r = s.get(f"{BASE_URL}/api/settings/logo")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert len(r.content) > 0

    # Reject non-image
    files = {"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")}
    r = s.post(f"{BASE_URL}/api/settings/logo", files=files)
    assert r.status_code == 422


# ---------- Employees ----------

def test_employees_crud_and_edge_cases(admin_session):
    s, admin = admin_session
    email = f"TEST_{uuid.uuid4().hex}@padaria.com"
    r = s.post(
        f"{BASE_URL}/api/employees",
        json={"name": "TEST Emp", "email": email, "password": "senha123", "role": "cashier"},
    )
    assert r.status_code == 200, r.text
    emp = r.json()
    assert emp["role"] == "cashier"
    assert emp["role_label"] == "Caixa"
    emp_id = emp["id"]

    # duplicate email → 409
    r = s.post(
        f"{BASE_URL}/api/employees",
        json={"name": "TEST Dup", "email": email, "password": "senha123", "role": "cashier"},
    )
    assert r.status_code == 409

    # list contains
    r = s.get(f"{BASE_URL}/api/employees")
    assert r.status_code == 200
    assert any(m["id"] == emp_id for m in r.json())

    # change role
    r = s.patch(f"{BASE_URL}/api/employees/{emp_id}", json={"role": "staff"})
    assert r.status_code == 200

    # invalid role → 422
    r = s.patch(f"{BASE_URL}/api/employees/{emp_id}", json={"role": "boss"})
    assert r.status_code == 422

    # cannot alter own role → 422
    r = s.patch(f"{BASE_URL}/api/employees/{admin['id']}", json={"role": "cashier"})
    assert r.status_code == 422

    # cannot delete own account → 422
    r = s.delete(f"{BASE_URL}/api/employees/{admin['id']}")
    assert r.status_code == 422

    # cleanup
    r = s.delete(f"{BASE_URL}/api/employees/{emp_id}")
    assert r.status_code == 200


# ---------- Cashier permissions ----------

@pytest.mark.parametrize("path", ["/api/reports/sales", "/api/register/history", "/api/employees", "/api/expenses"])
def test_cashier_blocked_from_admin_endpoints(cashier_session, path):
    s, _ = cashier_session
    r = s.get(f"{BASE_URL}{path}")
    assert r.status_code == 403, f"{path} → {r.status_code}"


def test_cashier_blocked_from_settings_put(cashier_session):
    s, _ = cashier_session
    r = s.put(f"{BASE_URL}/api/settings", json={"bakery_name": "Hack"})
    assert r.status_code == 403


def test_cashier_sees_admin_products(admin_session, cashier_session):
    admin_s, _ = admin_session
    cashier_s, _ = cashier_session
    # Ensure at least one product exists in the admin org
    admin_s.post(
        f"{BASE_URL}/api/products",
        json={"name": "TEST Compartilhado", "purchase_price": 4, "purchase_quantity": 2, "unit": "unidade"},
    )
    admin_products = admin_s.get(f"{BASE_URL}/api/products").json()
    cashier_products = cashier_s.get(f"{BASE_URL}/api/products").json()
    assert cashier_s.get(f"{BASE_URL}/api/products").status_code == 200
    admin_ids = {p["id"] for p in admin_products}
    cashier_ids = {p["id"] for p in cashier_products}
    assert admin_ids == cashier_ids and len(cashier_ids) > 0


# ---------- Expenses ----------

def test_expenses_crud_and_metrics(admin_session):
    s, _ = admin_session
    r = s.post(
        f"{BASE_URL}/api/expenses",
        json={"description": "TEST Aluguel", "category": "Aluguel", "amount": 1500, "due_date": "2026-01-31"},
    )
    assert r.status_code == 200, r.text
    exp = r.json()
    assert exp["status"] == "pendente"
    exp_id = exp["id"]

    # invalid status → 422
    r = s.patch(f"{BASE_URL}/api/expenses/{exp_id}", json={"status": "quitado"})
    assert r.status_code == 422

    # mark paid → summary reflects
    r = s.patch(f"{BASE_URL}/api/expenses/{exp_id}", json={"status": "pago"})
    assert r.status_code == 200

    listing = s.get(f"{BASE_URL}/api/expenses").json()
    assert any(e["id"] == exp_id and e["status"] == "pago" for e in listing)

    summary = s.get(f"{BASE_URL}/api/dashboard/summary").json()
    assert isinstance(summary["last_7_days"], list) and len(summary["last_7_days"]) == 7
    assert all("date" in d and "total" in d for d in summary["last_7_days"])
    assert "pending_expenses" in summary and "month_expenses_paid" in summary and "real_month_profit" in summary
    assert summary["month_expenses_paid"] >= 1500

    # reopen
    r = s.patch(f"{BASE_URL}/api/expenses/{exp_id}", json={"status": "pendente"})
    assert r.status_code == 200
