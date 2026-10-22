
import pytest
import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_orders.db")
    monkeypatch.setattr(app_module, "DATABASE_PATH", db_path)
    app_module.init_db()

    app_module.app.config.update(TESTING=True)
    with app_module.app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"FoodFlow" in response.data
    assert b"Veg Burger" in response.data


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_menu_endpoint(client):
    response = client.get("/api/menu")
    assert response.status_code == 200
    assert len(response.json) >= 1


def test_place_order(client):
    menu = client.get("/api/menu").json
    food = next(item for item in menu if item["name"] == "Veg Burger")

    response = client.post("/order", data={
        "customer_name": "Test Customer",
        "food_id": food["id"],
        "quantity": "2",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Order placed successfully" in response.data

    orders = client.get("/api/orders").json
    assert len(orders) == 1
    assert orders[0]["quantity"] == 2
    assert orders[0]["total"] == pytest.approx(198.00)


def test_invalid_quantity(client):
    menu = client.get("/api/menu").json

    response = client.post("/order", data={
        "customer_name": "Test Customer",
        "food_id": str(menu[0]["id"]),
        "quantity": "0",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Select a food item" in response.data
    assert len(client.get("/api/orders").json) == 0


def test_update_and_delete_order(client):
    food = client.get("/api/menu").json[0]

    client.post("/order", data={
        "customer_name": "Test Customer",
        "food_id": str(food["id"]),
        "quantity": "1",
    })

    order = client.get("/api/orders").json[0]

    response = client.post(
        f"/order/{order['id']}/status",
        data={"status": "Preparing"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert client.get("/api/orders").json[0]["status"] == "Preparing"

    response = client.post(
        f"/order/{order['id']}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert client.get("/api/orders").json == []
