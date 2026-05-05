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


@dataclass(frozen=True)
class StoreProfileUpdate:
    business_name: str
    tagline: str
    contact_name: str
    email: str
    phone: str
    city: str
    state: str
    instagram_url: str
    hero_image_url: str


@dataclass(frozen=True)
class ModelShotRequest:
    product_id: int
    source_image_url: str | None = None
    generated_image_url: str | None = None
    generation_mode: str | None = None
    status: str = "ready"
    notes: str | None = None


class StoreError(Exception):
    """Base exception for predictable store failures."""


class InventoryError(StoreError):
    """Raised when a checkout tries to buy unavailable inventory."""


class ProductNotFoundError(StoreError):
    """Raised when admin generation references a missing product."""


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
    if _table_count(connection, "store_profile") == 0:
        _insert_default_store_profile(connection)


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


def list_product_inventory(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            p.id,
            p.slug,
            p.name,
            p.category,
            p.image_url,
            p.price_cents,
            COALESCE(SUM(v.stock_quantity), 0) AS total_stock
        FROM products p
        LEFT JOIN variants v ON v.product_id = p.id
        GROUP BY p.id
        ORDER BY total_stock DESC, p.name ASC
        """
    ).fetchall()
    return [_inventory_from_row(row) for row in rows]


def get_product_inventory(connection: sqlite3.Connection, product_id: int) -> dict[str, Any] | None:
    return _get_product_inventory(connection, product_id)


def create_model_shot(connection: sqlite3.Connection, request: ModelShotRequest) -> dict[str, Any]:
    product = _get_product_inventory(connection, request.product_id)
    if product is None:
        raise ProductNotFoundError(f"Product {request.product_id} does not exist.")

    quality = quality_profile_for_stock(product["total_stock"])
    source_image_url = request.source_image_url or product["image_url"]
    generated_image_url = request.generated_image_url or product["image_url"]
    generation_mode = request.generation_mode or quality["generation_mode"]
    notes = request.notes or quality["notes"]

    with connection:
        cursor = connection.execute(
            """
            INSERT INTO generated_model_shots (
                product_id,
                source_image_url,
                generated_image_url,
                quality_tier,
                quality_label,
                generation_mode,
                stock_quantity,
                status,
                notes
            )
            VALUES (
                :product_id,
                :source_image_url,
                :generated_image_url,
                :quality_tier,
                :quality_label,
                :generation_mode,
                :stock_quantity,
                :status,
                :notes
            )
            """,
            {
                "product_id": product["id"],
                "source_image_url": source_image_url,
                "generated_image_url": generated_image_url,
                "quality_tier": quality["quality_tier"],
                "quality_label": quality["quality_label"],
                "generation_mode": generation_mode,
                "stock_quantity": product["total_stock"],
                "status": request.status,
                "notes": notes,
            },
        )
    shot = get_model_shot(connection, int(cursor.lastrowid))
    return shot


def list_model_shots(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT
            s.id,
            s.product_id,
            p.name AS product_name,
            p.category,
            s.source_image_url,
            s.generated_image_url,
            s.quality_tier,
            s.quality_label,
            s.generation_mode,
            s.stock_quantity,
            s.status,
            s.notes,
            s.created_at
        FROM generated_model_shots s
        JOIN products p ON p.id = s.product_id
        ORDER BY s.created_at DESC, s.id DESC
        LIMIT 12
        """
    ).fetchall()
    return [dict(row) for row in rows]


def get_model_shot(connection: sqlite3.Connection, shot_id: int) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            s.id,
            s.product_id,
            p.name AS product_name,
            p.category,
            s.source_image_url,
            s.generated_image_url,
            s.quality_tier,
            s.quality_label,
            s.generation_mode,
            s.stock_quantity,
            s.status,
            s.notes,
            s.created_at
        FROM generated_model_shots s
        JOIN products p ON p.id = s.product_id
        WHERE s.id = :shot_id
        """,
        {"shot_id": shot_id},
    ).fetchone()
    return dict(row)


def quality_profile_for_stock(total_stock: int) -> dict[str, Any]:
    if total_stock >= 20:
        return {
            "quality_tier": "premium",
            "quality_label": "Premium catalog render",
            "generation_mode": "product-to-model-quality",
            "notes": "High inventory supports spending more generation credits on a campaign-quality image.",
        }
    if total_stock >= 10:
        return {
            "quality_tier": "balanced",
            "quality_label": "Balanced listing render",
            "generation_mode": "product-to-model-balanced",
            "notes": "Moderate inventory gets a polished listing image without using the highest-cost mode.",
        }
    return {
        "quality_tier": "draft",
        "quality_label": "Draft low-stock preview",
        "generation_mode": "product-to-model-fast",
        "notes": "Low inventory gets a fast preview so expensive generation is reserved for better-stocked items.",
    }


def get_store_profile(connection: sqlite3.Connection) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT
            id,
            business_name,
            tagline,
            contact_name,
            email,
            phone,
            city,
            state,
            instagram_url,
            hero_image_url,
            updated_at
        FROM store_profile
        WHERE id = 1
        """
    ).fetchone()
    if row is None:
        _insert_default_store_profile(connection)
        row = connection.execute("SELECT * FROM store_profile WHERE id = 1").fetchone()
    return dict(row)


def update_store_profile(connection: sqlite3.Connection, profile: StoreProfileUpdate) -> dict[str, Any]:
    with connection:
        connection.execute(
            """
            UPDATE store_profile
            SET
                business_name = :business_name,
                tagline = :tagline,
                contact_name = :contact_name,
                email = :email,
                phone = :phone,
                city = :city,
                state = :state,
                instagram_url = :instagram_url,
                hero_image_url = :hero_image_url,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            {
                "business_name": profile.business_name,
                "tagline": profile.tagline,
                "contact_name": profile.contact_name,
                "email": profile.email.lower(),
                "phone": profile.phone,
                "city": profile.city,
                "state": profile.state.upper(),
                "instagram_url": profile.instagram_url,
                "hero_image_url": profile.hero_image_url,
            },
        )
    return get_store_profile(connection)


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


def _get_product_inventory(connection: sqlite3.Connection, product_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT
            p.id,
            p.slug,
            p.name,
            p.category,
            p.image_url,
            p.price_cents,
            COALESCE(SUM(v.stock_quantity), 0) AS total_stock
        FROM products p
        LEFT JOIN variants v ON v.product_id = p.id
        WHERE p.id = :product_id
        GROUP BY p.id
        """,
        {"product_id": product_id},
    ).fetchone()
    if row is None:
        return None
    return _inventory_from_row(row)


def _inventory_from_row(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["total_stock"] = int(payload["total_stock"])
    payload["quality_profile"] = quality_profile_for_stock(payload["total_stock"])
    return payload


def _insert_default_store_profile(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO store_profile (
            id,
            business_name,
            tagline,
            contact_name,
            email,
            phone,
            city,
            state,
            instagram_url,
            hero_image_url
        )
        VALUES (
            1,
            'Mom''s Clothing Biz',
            'Small-batch wardrobe staples picked with care.',
            'Maria Owner',
            'hello@momsclothingbiz.com',
            '(801) 555-0148',
            'Salt Lake City',
            'UT',
            'https://instagram.com/momsclothingbiz',
            'https://images.unsplash.com/photo-1445205170230-053b83016050?auto=format&fit=crop&w=1800&q=80'
        )
        """
    )
    connection.commit()


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
