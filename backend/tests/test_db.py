from __future__ import annotations

import unittest
from uuid import uuid4
from pathlib import Path

from app.db import (
    InventoryError,
    ModelShotRequest,
    OrderLine,
    OrderRequest,
    StoreProfileUpdate,
    category_sales_summary,
    connect,
    create_model_shot,
    create_order,
    get_product,
    get_store_profile,
    initialize_database,
    list_product_inventory,
    list_products,
    quality_profile_for_stock,
    update_store_profile,
)


class StoreDatabaseTest(unittest.TestCase):
    def setUp(self) -> None:
        scratch_root = Path(__file__).resolve().parents[1] / ".test-data"
        scratch_root.mkdir(exist_ok=True)
        self.db_path = scratch_root / f"store-{uuid4().hex}.db"
        self.connection = connect(self.db_path)
        initialize_database(self.connection)

    def tearDown(self) -> None:
        self.connection.close()
        self.db_path.unlink(missing_ok=True)

    def test_list_products_supports_category_size_and_search_filters(self) -> None:
        products = list_products(self.connection, category="Outerwear", size="M", query="denim")

        self.assertEqual(1, len(products))
        self.assertEqual("Weekend Denim Jacket", products[0]["name"])
        self.assertIn("M", products[0]["available_sizes"])

    def test_get_product_includes_variants(self) -> None:
        product = get_product(self.connection, 1)

        self.assertIsNotNone(product)
        self.assertGreaterEqual(len(product["variants"]), 1)
        self.assertIn("stock_quantity", product["variants"][0])

    def test_create_order_persists_customer_items_and_updates_stock(self) -> None:
        before = self.connection.execute(
            "SELECT stock_quantity FROM variants WHERE id = 1"
        ).fetchone()["stock_quantity"]

        order = create_order(
            self.connection,
            OrderRequest(
                email="customer@example.com",
                full_name="Avery Customer",
                city="Salt Lake City",
                state="UT",
                items=[OrderLine(variant_id=1, quantity=2)],
            ),
        )

        after = self.connection.execute(
            "SELECT stock_quantity FROM variants WHERE id = 1"
        ).fetchone()["stock_quantity"]

        self.assertEqual(before - 2, after)
        self.assertEqual(12800, order["subtotal_cents"])
        self.assertEqual(1, len(order["items"]))

    def test_create_order_rejects_out_of_stock_purchase(self) -> None:
        with self.assertRaises(InventoryError):
            create_order(
                self.connection,
                OrderRequest(
                    email="customer@example.com",
                    full_name="Avery Customer",
                    city="Salt Lake City",
                    state="UT",
                    items=[OrderLine(variant_id=1, quantity=999)],
                ),
            )

    def test_category_sales_summary_uses_joined_aggregation(self) -> None:
        create_order(
            self.connection,
            OrderRequest(
                email="customer@example.com",
                full_name="Avery Customer",
                city="Salt Lake City",
                state="UT",
                items=[OrderLine(variant_id=1, quantity=1), OrderLine(variant_id=5, quantity=1)],
            ),
        )

        summary = category_sales_summary(self.connection)

        self.assertEqual(["Outerwear", "Tops"], [row["category"] for row in summary])
        self.assertEqual(9800, summary[0]["revenue_cents"])
        self.assertEqual(6400, summary[1]["revenue_cents"])

    def test_store_profile_can_be_updated_for_admin_demo(self) -> None:
        original = get_store_profile(self.connection)

        updated = update_store_profile(
            self.connection,
            StoreProfileUpdate(
                business_name="Maria's Closet",
                tagline="Polished outfits for weekday errands and weekend plans.",
                contact_name="Maria Sanchez",
                email="maria@example.com",
                phone="801-555-0199",
                city="Murray",
                state="ut",
                instagram_url="https://instagram.com/mariascloset",
                hero_image_url="/uploads/profile-demo.png",
            ),
        )

        self.assertEqual(1, original["id"])
        self.assertEqual("Maria's Closet", updated["business_name"])
        self.assertEqual("maria@example.com", updated["email"])
        self.assertEqual("UT", updated["state"])

    def test_quality_profile_changes_with_stock(self) -> None:
        self.assertEqual("premium", quality_profile_for_stock(20)["quality_tier"])
        self.assertEqual("balanced", quality_profile_for_stock(10)["quality_tier"])
        self.assertEqual("draft", quality_profile_for_stock(4)["quality_tier"])

    def test_create_model_shot_uses_stock_driven_quality(self) -> None:
        self.connection.execute(
            """
            UPDATE variants
            SET stock_quantity = 1
            WHERE product_id = 4
            """
        )
        self.connection.commit()

        shot = create_model_shot(
            self.connection,
            ModelShotRequest(product_id=4, source_image_url="/uploads/source-dress.png"),
        )
        inventory = list_product_inventory(self.connection)

        self.assertEqual("Market Day Midi Dress", shot["product_name"])
        self.assertEqual("draft", shot["quality_tier"])
        self.assertEqual(4, shot["stock_quantity"])
        self.assertTrue(any(item["id"] == 4 for item in inventory))


if __name__ == "__main__":
    unittest.main()
