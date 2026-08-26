"""Backend tests for the 4 new modules: Production, Finance history, Reports, Customer purchases."""
import os
import uuid
import requests
from pathlib import Path


def _load_base_url():
    env = os.environ.get("REACT_APP_BACKEND_URL")
    if env:
        return env.rstrip("/")
    env_file = Path(__file__).resolve().parents[2] / "frontend" / ".env"
    for line in env_file.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_base_url()


def _auth_session():
    s = requests.Session()
    email = f"TEST_{uuid.uuid4().hex[:8]}@example.com"
    r = s.post(f"{BASE_URL}/api/auth/register",
               json={"name": "New Modules Test", "email": email, "password": "padaria123"})
    assert r.status_code == 200, r.text
    return s


# ---------- Production ----------
def test_production_deducts_ingredients_and_increases_product_stock():
    s = _auth_session()
    ing = s.post(f"{BASE_URL}/api/ingredients",
                 json={"name": "TEST Farinha", "purchase_price": 50, "purchase_quantity": 5000, "unit": "g"}).json()
    recipe = s.post(f"{BASE_URL}/api/recipes",
                    json={"name": "TEST Pao Receita", "yield_quantity": 20,
                          "ingredients": [{"ingredient_id": ing["id"], "quantity": 1000}]}).json()
    product = s.post(f"{BASE_URL}/api/products",
                     json={"name": "TEST Pao Novo", "category": "Salgados", "sale_price": 1.5,
                           "stock_quantity": 0, "recipe_id": recipe["id"]}).json()

    r = s.post(f"{BASE_URL}/api/production", json={"recipe_id": recipe["id"], "quantity": 40})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["quantity"] == 40
    assert body["recipe_id"] == recipe["id"]
    assert body["products_updated"] == 1
    assert body["ingredient_cost"] == 20.0  # unit_cost 0.01 * 1000 = cost_total 10; factor 2 → 20
    assert "_id" not in body

    # Ingredient: 5000 - (1000 * 40/20)=2000 → 3000
    ings = s.get(f"{BASE_URL}/api/ingredients").json()
    updated_ing = next(i for i in ings if i["id"] == ing["id"])
    assert updated_ing["stock_quantity"] == 3000

    # Product stock: 0 + 40 = 40
    products = s.get(f"{BASE_URL}/api/products").json()
    updated_prod = next(p for p in products if p["id"] == product["id"])
    assert updated_prod["stock_quantity"] == 40

    listing = s.get(f"{BASE_URL}/api/production").json()
    assert any(p["recipe_id"] == recipe["id"] and p["quantity"] == 40 for p in listing)


def test_production_invalid_recipe_returns_404():
    s = _auth_session()
    r = s.post(f"{BASE_URL}/api/production", json={"recipe_id": "does-not-exist", "quantity": 5})
    assert r.status_code == 404


# ---------- Finance history ----------
def test_register_history_only_returns_closed_with_totals():
    s = _auth_session()
    # Open, add a sale, close
    s.post(f"{BASE_URL}/api/register/open", json={"opening_balance": 100})
    sale = s.post(f"{BASE_URL}/api/sales",
                  json={"items": [{"product_name": "TEST Item", "quantity": 2, "unit_price": 5}],
                        "payments": [{"method": "Dinheiro", "amount": 10}]})
    assert sale.status_code == 200, sale.text
    s.post(f"{BASE_URL}/api/register/movement", json={"type": "sangria", "amount": 3})
    s.post(f"{BASE_URL}/api/register/movement", json={"type": "suprimento", "amount": 7})
    close = s.post(f"{BASE_URL}/api/register/close", json={"counted_amount": 114})
    assert close.status_code == 200, close.text

    history = s.get(f"{BASE_URL}/api/register/history")
    assert history.status_code == 200
    sessions = history.json()
    assert len(sessions) >= 1
    for sess in sessions:
        assert sess["status"] == "closed"
        assert "sales_total" in sess and "sales_count" in sess
        assert "sangrias" in sess and "suprimentos" in sess
    last = sessions[0]
    assert last["sales_count"] == 1
    assert last["sales_total"] == 10
    assert last["sangrias"] == 3
    assert last["suprimentos"] == 7


# ---------- Reports ----------
def test_reports_sales_periods_and_totals():
    s = _auth_session()
    # Seed a product+sale
    s.post(f"{BASE_URL}/api/products",
           json={"name": "TEST Report Prod", "purchase_price": 2, "purchase_quantity": 1,
                 "sale_price": 5, "category": "Doces"})
    s.post(f"{BASE_URL}/api/sales",
           json={"items": [{"product_name": "TEST Report Prod", "quantity": 3, "unit_price": 5}],
                 "payments": [{"method": "PIX", "amount": 15}]})

    for period in ("day", "month", "all", "invalid-falls-back-to-all"):
        r = s.get(f"{BASE_URL}/api/reports/sales", params={"period": period})
        assert r.status_code == 200, f"{period}: {r.text}"
        body = r.json()
        assert "rows" in body and "totals" in body
        # totals fields
        for key in ("quantity", "revenue", "cost", "profit", "margin"):
            assert key in body["totals"]

    all_report = s.get(f"{BASE_URL}/api/reports/sales", params={"period": "all"}).json()
    row = next(r for r in all_report["rows"] if r["product_name"] == "TEST Report Prod")
    assert row["quantity"] == 3
    assert row["revenue"] == 15
    assert row["cost"] == 6  # unit_cost=2 * 3
    assert row["profit"] == 9
    assert row["margin"] == 60.0
    # Rows sorted by revenue desc
    revs = [r["revenue"] for r in all_report["rows"]]
    assert revs == sorted(revs, reverse=True)


# ---------- Customer purchases + customer_id on sale ----------
def test_sale_links_customer_and_purchases_endpoint():
    s = _auth_session()
    customer = s.post(f"{BASE_URL}/api/customers",
                      json={"name": "TEST Maria", "phone": "11999999999"}).json()

    sale = s.post(f"{BASE_URL}/api/sales",
                  json={"items": [{"product_name": "TEST Cli Prod", "quantity": 1, "unit_price": 7.5}],
                        "payments": [{"method": "PIX", "amount": 7.5}],
                        "customer_id": customer["id"], "customer_name": customer["name"]})
    assert sale.status_code == 200, sale.text
    assert sale.json()["customer_id"] == customer["id"]

    r = s.get(f"{BASE_URL}/api/customers/{customer['id']}/purchases")
    assert r.status_code == 200
    purchases = r.json()
    assert len(purchases) == 1
    assert purchases[0]["customer_id"] == customer["id"]
    assert purchases[0]["total"] == 7.5

    # Empty for random id
    empty = s.get(f"{BASE_URL}/api/customers/{uuid.uuid4()}/purchases")
    assert empty.status_code == 200
    assert empty.json() == []
