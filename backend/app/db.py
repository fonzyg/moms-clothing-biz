from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR.parent / "data" / "store.db"


@dataclass(frozen=True)
class OrderLine:
    variant_id: int
    quantity: int


@dataclass(frozen=True)
class OrderRequest:
    email: str
    full_name: str
    city: str
    state: str
    items: list[OrderLine]


class StoreError(Exception):
    """Base exception for predictable store failures."""


class InventoryError(StoreError):
    """Raised when a checkout tries to buy unavailable inventory."""


def connect(database_path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(database_path) if database_path else DEFAULT_DATABASE
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    _execute_script(connection, BASE_DIR / "sql" / "schema.sql")
    if _table_count(connection, "products") == 0:
        _execute_script(connection, BASE_DIR / "sql" / "seed.sql")


def list_products(
    connection: sqlite3.Connection,
    *,
    category: str | None = None,
    size: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    sql = """
        SELECT
            p.id,
            p.slug,
            p.name,
            p.category,
            p.description,
            p.price_cents,
            p.image_url,
            p.is_featured,
            SUM(v.stock_quantity) AS total_stock,
            GROUP_CONCAT(DISTINCT v.size) AS available_sizes,
            GROUP_CONCAT(DISTINCT v.color) AS available_colors
        FROM products p
        JOIN variants v ON v.product_id = p.id
        WHERE 1 = 1
    """
    params: dict[str, Any] = {}

    if category:
        sql += " AND p.category = :category"
        params["category"] = category

    if size:
        sql += """
            AND EXISTS (
                SELECT 1
                FROM variants size_variant
                WHERE size_variant.product_id = p.id
                  AND size_variant.size = :size
                  AND size_variant.stock_quantity > 0
            )
        """
        params["size"] = size

    if query:
        sql += " AND (LOWER(p.name) LIKE :query OR LOWER(p.description) LIKE :query)"
        params["query"] = f"%{query.lower()}%"

    sql += """
        GROUP BY p.id
        HAVING total_stock > 0
        ORDER BY p.is_featured DESC, p.name ASC
    """

    return [_product_from_row(row) for row in connection.execute(sql, params).fetchall()]


def list_categories(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT DISTINCT category
        FROM products
        ORDER BY category ASC
        """
    ).fetchall()
    return [row["category"] for row in rows]


def list_sizes(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        """
        SELECT DISTINCT size
        FROM variants
        WHERE stock_quantity > 0
        ORDER BY
            CASE size
                WHEN 'XS' THEN 1
                WHEN 'S' THEN 2
                WHEN 'M' THEN 3
                WHEN 'L' THEN 4
                WHEN 'XL' THEN 5
                ELSE 6
            END
        """
    ).fetchall()
    return [row["size"] for row in rows]


def get_product(connection: sqlite3.Connection, product_id: int) -> dict[str, Any] | None:
    product = connection.execute(
        """
        SELECT
            p.id,
            p.slug,
            p.name,
            p.category,
            p.description,
            p.price_cents,
            p.image_url,
            p.is_featured,
            SUM(v.stock_quantity) AS total_stock,
            GROUP_CONCAT(DISTINCT v.size) AS available_sizes,
            GROUP_CONCAT(DISTINCT v.color) AS available_colors
        FROM products p
        JOIN variants v ON v.product_id = p.id
        WHERE p.id = :product_id
        GROUP BY p.id
        """,
        {"product_id": product_id},
    ).fetchone()

    if product is None:
        return None

    variants = connection.execute(
        """
        SELECT id, size, color, stock_quantity
        FROM variants
        WHERE product_id = :product_id
        ORDER BY size, color
        """,
        {"product_id": product_id},
    ).fetchall()

    payload = _product_from_row(product)
    payload["variants"] = [dict(row) for row in variants]
    return payload


def create_order(connection: sqlite3.Connection, request: OrderRequest) -> dict[str, Any]:
    if not request.items:
        raise InventoryError("Order must include at least one item.")

    with connection:
        customer_id = _upsert_customer(connection, request)
        priced_lines: list[dict[str, Any]] = []

        for item in request.items:
            variant = connection.execute(
                """
                SELECT
                    v.id AS variant_id,
                    v.stock_quantity,
                    v.size,
                    v.color,
                    p.id AS product_id,
                    p.name AS product_name,
                    p.price_cents
                FROM variants v
                JOIN products p ON p.id = v.product_id
                WHERE v.id = :variant_id
                """,
                {"variant_id": item.variant_id},
            ).fetchone()

            if variant is None:
                raise InventoryError(f"Variant {item.variant_id} does not exist.")
            if variant["stock_quantity"] < item.quantity:
                raise InventoryError(
                    f"Only {variant['stock_quantity']} left for {variant['product_name']} "
                    f"({variant['size']} / {variant['color']})."
                )

            priced_lines.append(
                {
                    "variant_id": variant["variant_id"],
                    "product_name": variant["product_name"],
                    "size": variant["size"],
                    "color": variant["color"],
                    "quantity": item.quantity,
                    "unit_price_cents": variant["price_cents"],
                }
            )

        subtotal_cents = sum(line["quantity"] * line["unit_price_cents"] for line in priced_lines)
        order_cursor = connection.execute(
            """
            INSERT INTO orders (customer_id, subtotal_cents)
            VALUES (:customer_id, :subtotal_cents)
            """,
            {"customer_id": customer_id, "subtotal_cents": subtotal_cents},
        )
        order_id = int(order_cursor.lastrowid)

        for line in priced_lines:
            connection.execute(
                """
                INSERT INTO order_items (order_id, variant_id, quantity, unit_price_cents)
                VALUES (:order_id, :variant_id, :quantity, :unit_price_cents)
                """,
                {
                    "order_id": order_id,
                    "variant_id": line["variant_id"],
                    "quantity": line["quantity"],
                    "unit_price_cents": line["unit_price_cents"],
                },
            )
            connection.execute(
                """
                UPDATE variants
                SET stock_quantity = stock_quantity - :quantity
                WHERE id = :variant_id
                """,
                {"variant_id": line["variant_id"], "quantity": line["quantity"]},
            )

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "subtotal_cents": subtotal_cents,
        "items": priced_lines,
    }


def category_sales_summary(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            p.category,
            COUNT(DISTINCT o.id) AS order_count,
            SUM(oi.quantity) AS units_sold,
            SUM(oi.quantity * oi.unit_price_cents) AS revenue_cents
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        JOIN variants v ON v.id = oi.variant_id
        JOIN products p ON p.id = v.product_id
        WHERE o.status = 'placed'
        GROUP BY p.category
        ORDER BY revenue_cents DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _execute_script(connection: sqlite3.Connection, path: Path) -> None:
    connection.executescript(path.read_text(encoding="utf-8"))
    connection.commit()


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"])


def _upsert_customer(connection: sqlite3.Connection, request: OrderRequest) -> int:
    connection.execute(
        """
        INSERT INTO customers (email, full_name, city, state)
        VALUES (:email, :full_name, :city, :state)
        ON CONFLICT(email) DO UPDATE SET
            full_name = excluded.full_name,
            city = excluded.city,
            state = excluded.state
        """,
        {
            "email": request.email.lower(),
            "full_name": request.full_name,
            "city": request.city,
            "state": request.state,
        },
    )
    row = connection.execute(
        "SELECT id FROM customers WHERE email = :email",
        {"email": request.email.lower()},
    ).fetchone()
    return int(row["id"])


def _product_from_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["available_sizes"] = _split_csv(payload.get("available_sizes"))
    payload["available_colors"] = _split_csv(payload.get("available_colors"))
    payload["is_featured"] = bool(payload["is_featured"])
    return payload


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return sorted({item for item in value.split(",") if item})
