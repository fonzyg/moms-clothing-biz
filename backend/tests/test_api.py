from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient


def test_product_api_returns_seeded_catalog(monkeypatch):
    scratch_root = Path(__file__).resolve().parents[1] / ".test-data"
    scratch_root.mkdir(exist_ok=True)
    db_path = scratch_root / f"store-{uuid4().hex}.db"
    try:
        monkeypatch.setenv("STORE_DATABASE_PATH", str(db_path))

        from app.main import app, database_path

        database_path.cache_clear()
        with TestClient(app) as client:
            response = client.get("/api/products?category=Outerwear")

        assert response.status_code == 200
        names = {product["name"] for product in response.json()}
        assert "Weekend Denim Jacket" in names
    finally:
        db_path.unlink(missing_ok=True)


def test_checkout_endpoint_creates_order(monkeypatch):
    scratch_root = Path(__file__).resolve().parents[1] / ".test-data"
    scratch_root.mkdir(exist_ok=True)
    db_path = scratch_root / f"store-{uuid4().hex}.db"
    try:
        monkeypatch.setenv("STORE_DATABASE_PATH", str(db_path))

        from app.main import app, database_path

        database_path.cache_clear()
        with TestClient(app) as client:
            response = client.post(
                "/api/orders",
                json={
                    "email": "shopper@example.com",
                    "full_name": "Shopper Example",
                    "city": "Ogden",
                    "state": "UT",
                    "items": [{"variant_id": 1, "quantity": 1}],
                },
            )

        assert response.status_code == 201
        assert response.json()["subtotal_cents"] == 6400
    finally:
        db_path.unlink(missing_ok=True)
