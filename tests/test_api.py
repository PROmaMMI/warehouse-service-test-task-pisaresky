import pytest
from datetime import datetime
from uuid import UUID

from fastapi.testclient import TestClient
from app.main import app, crud

client = TestClient(app)

class DummyMovement:
    def __init__(
        self,
        movement_id,
        product_id,
        source_warehouse_id,
        departure_time,
        destination_warehouse_id,
        arrival_time,
        quantity_departure,
        quantity_arrival,
    ):
        self.movement_id = UUID(movement_id)
        self.product_id = UUID(product_id)
        self.source_warehouse_id = UUID(source_warehouse_id)
        self.departure_time = departure_time
        self.destination_warehouse_id = UUID(destination_warehouse_id)
        self.arrival_time = arrival_time
        self.quantity_departure = quantity_departure
        self.quantity_arrival = quantity_arrival


class DummyInventory:
    def __init__(self, warehouse_id, product_id, quantity):
        self.warehouse_id = UUID(warehouse_id)
        self.product_id = UUID(product_id)
        self.quantity = quantity


def test_read_movement_success(monkeypatch):
    movement_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    product_id = "4705204f-498f-4f96-b4ba-df17fb56bf55"
    source_warehouse_id = "c1d70455-7e14-11e9-812a-70106f431230"
    destination_warehouse_id = "d2e81566-8f25-22f0-923b-81217e542341"
    departure_time = datetime(2025, 6, 6, 15, 0, 0)
    arrival_time = datetime(2025, 6, 6, 16, 0, 0)

    dummy_mv = DummyMovement(
        movement_id,
        product_id,
        source_warehouse_id,
        departure_time,
        destination_warehouse_id,
        arrival_time,
        100,
        90,
    )

    monkeypatch.setattr(crud, "get_movement_by_id", lambda db, mv_id: dummy_mv)

    response = client.get(f"/api/movements/{movement_id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["movement_id"] == movement_id
    assert payload["product_id"] == product_id
    assert payload["source_warehouse_id"] == source_warehouse_id
    assert payload["destination_warehouse_id"] == destination_warehouse_id
    assert payload["time_diff_seconds"] == 3600
    assert payload["quantity_diff"] == -10
    assert payload["quantity_departure"] == 100
    assert payload["quantity_arrival"] == 90


def test_read_movement_not_found(monkeypatch):
    monkeypatch.setattr(crud, "get_movement_by_id", lambda db, mv_id: None)
    response = client.get("/api/movements/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    assert response.status_code == 404
    assert response.json()["detail"] == "Движение не найдено"


def test_read_movement_partial_data(monkeypatch):
    dummy_mv = DummyMovement(
        movement_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        product_id="11111111-1111-1111-1111-111111111111",
        source_warehouse_id="22222222-2222-2222-2222-222222222222",
        departure_time=datetime(2025, 6, 6, 15, 0, 0),
        destination_warehouse_id="33333333-3333-3333-3333-333333333333",
        arrival_time=None,
        quantity_departure=100,
        quantity_arrival=None,
    )

    monkeypatch.setattr(crud, "get_movement_by_id", lambda db, mv_id: dummy_mv)
    response = client.get("/api/movements/cccccccc-cccc-cccc-cccc-cccccccccccc")
    assert response.status_code == 200
    payload = response.json()

    assert payload["time_diff_seconds"] is None
    assert payload["quantity_diff"] is None
    assert payload["quantity_departure"] == 100
    assert payload["quantity_arrival"] is None


def test_read_inventory_success(monkeypatch):
    warehouse_id = "c1d70455-7e14-11e9-812a-70106f431230"
    product_id = "4705204f-498f-4f96-b4ba-df17fb56bf55"
    dummy_inv = DummyInventory(warehouse_id, product_id, 77)

    monkeypatch.setattr(crud, "get_inventory", lambda db, wh_id, pr_id: dummy_inv)

    response = client.get(f"/api/warehouses/{warehouse_id}/products/{product_id}")
    assert response.status_code == 200
    payload = response.json()

    assert payload["warehouse_id"] == warehouse_id
    assert payload["product_id"] == product_id
    assert payload["quantity"] == 77


def test_read_inventory_not_found(monkeypatch):
    monkeypatch.setattr(crud, "get_inventory", lambda db, wh_id, pr_id: None)

    warehouse_id = "00000000-0000-0000-0000-000000000000"
    product_id = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/api/warehouses/{warehouse_id}/products/{product_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Inventory not found"