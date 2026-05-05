from __future__ import annotations

import unittest
from uuid import uuid4
from pathlib import Path

from app.db import (
    InventoryError,
    OrderLine,
    OrderRequest,
    category_sales_summary,
    connect,
    create_order,
    get_product,
    initialize_database,
    list_products,
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


if __name__ == "__main__":
    unittest.main()
