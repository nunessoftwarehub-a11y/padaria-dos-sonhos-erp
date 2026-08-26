"""Tests for register (caixa), split payments, stock deduction, and dashboard summary."""
import os
import uuid
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _register_user():
    session = requests.Session()
    email = f"TEST_{uuid.uuid4().hex}@example.com"
    r = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"name": "Register Test", "email": email, "password": "padaria123"},
    )
    assert r.status_code == 200, r.text
    return session


def test_register_open_movement_close_flow():
    s = _register_user()
    # Open register
    r = s.post(f"{BASE_URL}/api/register/open", json={"opening_balance": 50})
    assert r.status_code == 200
    session_data = r.json()
    assert session_data["status"] == "open"
    assert session_data["opening_balance"] == 50

    # Duplicate open should 409
    r2 = s.post(f"{BASE_URL}/api/register/open", json={"opening_balance": 30})
    assert r2.status_code == 409

    # Current
    cur = s.get(f"{BASE_URL}/api/register/current").json()
    assert cur["status"] == "open"
    assert cur["expected_cash"] == 50
    assert cur["sales_count"] == 0

    # Suprimento +20 and sangria -5
    assert s.post(f"{BASE_URL}/api/register/movement", json={"type": "suprimento", "amount": 20}).status_code == 200
    assert s.post(f"{BASE_URL}/api/register/movement", json={"type": "sangria", "amount": 5}).status_code == 200
    cur = s.get(f"{BASE_URL}/api/register/current").json()
    assert cur["suprimentos"] == 20
    assert cur["sangrias"] == 5
    assert cur["expected_cash"] == 65  # 50 + 20 - 5

    # Invalid movement
    bad = s.post(f"{BASE_URL}/api/register/movement", json={"type": "outro", "amount": 3})
    assert bad.status_code == 422

    # Close
    close = s.post(f"{BASE_URL}/api/register/close", json={"counted_amount": 65})
    assert close.status_code == 200
    body = close.json()
    assert body["difference"] == 0
    assert body["expected_cash"] == 65

    # No open session after close
    assert s.get(f"{BASE_URL}/api/register/current").json()["status"] == "closed"


def test_sale_split_payment_and_stock_and_recipe_deduction():
    s = _register_user()
    s.post(f"{BASE_URL}/api/register/open", json={"opening_balance": 0})

    # Create ingredient with stock=3
    ing = s.post(
        f"{BASE_URL}/api/ingredients",
        json={"name": "TEST Farinha", "purchase_price": 6, "purchase_quantity": 3, "unit": "kg"},
    ).json()
    assert ing["stock_quantity"] == 3

    # Recipe yields 2, uses 1 farinha per batch
    rec = s.post(
        f"{BASE_URL}/api/recipes",
        json={
            "name": "TEST Pao Recipe",
            "yield_quantity": 2,
            "ingredients": [{"ingredient_id": ing["id"], "quantity": 1}],
        },
    ).json()

    # Product linked to recipe with stock=50
    prod = s.post(
        f"{BASE_URL}/api/products",
        json={
            "name": "TEST Pao PDV",
            "sale_price": 5,
            "stock_quantity": 50,
            "min_stock": 10,
            "recipe_id": rec["id"],
        },
    ).json()
    assert prod["stock_quantity"] == 50

    # Split sale: 2 units * 5 = 10 = 6 Dinheiro + 4 PIX
    sale_payload = {
        "items": [{"product_name": prod["name"], "product_id": prod["id"], "quantity": 2, "unit_price": 5}],
        "payments": [{"method": "Dinheiro", "amount": 6}, {"method": "PIX", "amount": 4}],
    }
    sale = s.post(f"{BASE_URL}/api/sales", json=sale_payload)
    assert sale.status_code == 200, sale.text
    sdata = sale.json()
    assert sdata["total"] == 10
    assert "Dinheiro" in sdata["payment_method"]

    # Split with wrong sum should 422
    bad = s.post(
        f"{BASE_URL}/api/sales",
        json={
            "items": [{"product_name": prod["name"], "product_id": prod["id"], "quantity": 1, "unit_price": 5}],
            "payments": [{"method": "Dinheiro", "amount": 3}, {"method": "PIX", "amount": 1}],
        },
    )
    assert bad.status_code == 422

    # Verify product stock decreased by 2 -> 48
    products = s.get(f"{BASE_URL}/api/products").json()
    p_after = next(p for p in products if p["id"] == prod["id"])
    assert p_after["stock_quantity"] == 48

    # Verify ingredient stock decreased: quantity 1 * 2 / yield 2 = 1 => 3 - 1 = 2
    ingredients = s.get(f"{BASE_URL}/api/ingredients").json()
    i_after = next(i for i in ingredients if i["id"] == ing["id"])
    assert abs(i_after["stock_quantity"] - 2) < 0.01

    # Register summary reflects sale + cash
    cur = s.get(f"{BASE_URL}/api/register/current").json()
    assert cur["sales_count"] == 1
    assert cur["totals_by_method"].get("Dinheiro") == 6
    assert cur["totals_by_method"].get("PIX") == 4
    assert cur["expected_cash"] == 6  # opening 0 + cash 6


def test_dashboard_summary_reflects_sales_and_low_stock():
    s = _register_user()
    s.post(f"{BASE_URL}/api/register/open", json={"opening_balance": 0})
    prod = s.post(
        f"{BASE_URL}/api/products",
        json={
            "name": "TEST LowStock",
            "sale_price": 10,
            "purchase_price": 4,
            "purchase_quantity": 1,
            "stock_quantity": 3,
            "min_stock": 5,
        },
    ).json()
    # Sale of 1 unit at 10
    s.post(
        f"{BASE_URL}/api/sales",
        json={
            "items": [{"product_name": prod["name"], "product_id": prod["id"], "quantity": 1, "unit_price": 10}],
            "payment_method": "Dinheiro",
        },
    )
    s.post(f"{BASE_URL}/api/register/movement", json={"type": "sangria", "amount": 2})

    summary = s.get(f"{BASE_URL}/api/dashboard/summary").json()
    assert summary["day_total"] >= 10
    assert summary["day_expenses"] >= 2
    # low_stock should include our product (stock 2 <= min 5)
    assert any(p["id"] == prod["id"] for p in summary["low_stock"])
    assert len(summary["recent_sales"]) >= 1
