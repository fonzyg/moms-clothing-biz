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

        from app.main import app, database_path, uploads_path

        database_path.cache_clear()
        uploads_path.cache_clear()
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

        from app.main import app, database_path, uploads_path

        database_path.cache_clear()
        uploads_path.cache_clear()
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


def test_admin_profile_endpoint_updates_contact_info_and_picture(monkeypatch):
    scratch_root = Path(__file__).resolve().parents[1] / ".test-data"
    scratch_root.mkdir(exist_ok=True)
    db_path = scratch_root / f"store-{uuid4().hex}.db"
    try:
        monkeypatch.setenv("STORE_DATABASE_PATH", str(db_path))

        from app.main import app, database_path, uploads_path

        database_path.cache_clear()
        uploads_path.cache_clear()
        tiny_png = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )
        with TestClient(app) as client:
            response = client.put(
                "/api/admin/store-profile",
                json={
                    "business_name": "Maria's Closet",
                    "tagline": "Polished outfits for weekday errands and weekend plans.",
                    "contact_name": "Maria Sanchez",
                    "email": "maria@example.com",
                    "phone": "801-555-0199",
                    "city": "Murray",
                    "state": "UT",
                    "instagram_url": "https://instagram.com/mariascloset",
                    "hero_image_url": "/uploads/old-profile.png",
                    "hero_image_data_url": tiny_png,
                },
            )
            saved = client.get("/api/store-profile")

        assert response.status_code == 200
        payload = response.json()
        assert payload["business_name"] == "Maria's Closet"
        assert payload["hero_image_url"].startswith("/uploads/profile-")
        assert saved.json()["phone"] == "801-555-0199"
    finally:
        db_path.unlink(missing_ok=True)


def test_admin_model_shot_endpoint_uses_inventory_quality(monkeypatch):
    scratch_root = Path(__file__).resolve().parents[1] / ".test-data"
    scratch_root.mkdir(exist_ok=True)
    db_path = scratch_root / f"store-{uuid4().hex}.db"
    try:
        monkeypatch.setenv("STORE_DATABASE_PATH", str(db_path))

        from app.main import app, database_path, uploads_path

        database_path.cache_clear()
        uploads_path.cache_clear()
        tiny_png = (
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )
        with TestClient(app) as client:
            inventory = client.get("/api/admin/products/inventory")
            response = client.post(
                "/api/admin/model-shots",
                json={
                    "product_id": 5,
                    "source_image_data_url": tiny_png,
                },
            )
            shots = client.get("/api/admin/model-shots")

        assert inventory.status_code == 200
        assert inventory.json()[0]["quality_profile"]["quality_tier"] == "premium"
        assert response.status_code == 201
        payload = response.json()
        assert payload["product_name"] == "Tailored Work Trouser"
        assert payload["quality_tier"] == "premium"
        assert payload["source_image_url"].startswith("/uploads/garment-")
        assert shots.json()[0]["product_name"] == "Tailored Work Trouser"
    finally:
        db_path.unlink(missing_ok=True)
