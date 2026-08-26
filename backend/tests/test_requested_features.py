"""Regression coverage for product, ingredient, recipe, sale and customer flows."""
import os
import uuid

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def test_requested_crud_and_cost_calculations():
    assert BASE_URL, "REACT_APP_BACKEND_URL is required"
    session = requests.Session()
    email = f"TEST_{uuid.uuid4().hex}@example.com"
    register = session.post(
        f"{BASE_URL}/api/auth/register",
        json={"name": "Feature Test", "email": email, "password": "padaria123"},
    )
    assert register.status_code == 200

    product = session.post(
        f"{BASE_URL}/api/products",
        json={"name": "TEST Pao", "purchase_price": 10, "purchase_quantity": 5, "unit": "kg", "sale_price": 7},
    )
    assert product.status_code == 200
    product_data = product.json()
    assert product_data["unit_cost"] == 2
    assert product_data["suggested_sale_price"] == 5
    assert any(item["id"] == product_data["id"] for item in session.get(f"{BASE_URL}/api/products").json())

    ingredient = session.post(
        f"{BASE_URL}/api/ingredients",
        json={"name": "TEST Farinha", "purchase_price": 12, "purchase_quantity": 3, "unit": "kg"},
    )
    assert ingredient.status_code == 200
    ingredient_data = ingredient.json()
    assert ingredient_data["unit_cost"] == 4
    assert "_id" not in ingredient_data

    recipe = session.post(
        f"{BASE_URL}/api/recipes",
        json={"name": "TEST Receita", "yield_quantity": 2, "ingredients": [{"ingredient_id": ingredient_data["id"], "quantity": 2}]},
    )
    assert recipe.status_code == 200
    recipe_data = recipe.json()
    assert recipe_data["cost_total"] == 8
    assert recipe_data["cost_per_unit"] == 4
    assert "_id" not in recipe_data

    sale = session.post(
        f"{BASE_URL}/api/sales",
        json={"product_name": "TEST Pao", "quantity": 1, "total": 5, "payment_method": "PIX"},
    )
    assert sale.status_code == 200
    assert sale.json()["payment_method"] == "PIX"

    customer = session.post(f"{BASE_URL}/api/customers", json={"name": "TEST Cliente", "phone": "5511999999999"})
    assert customer.status_code == 200
    assert customer.json()["name"] == "TEST Cliente"