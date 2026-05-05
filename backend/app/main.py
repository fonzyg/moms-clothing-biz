from __future__ import annotations

import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from app.db import (
    InventoryError,
    OrderLine,
    OrderRequest,
    category_sales_summary,
    connect,
    create_order,
    get_product,
    initialize_database,
    list_categories,
    list_products,
    list_sizes,
)


class VariantResponse(BaseModel):
    id: int
    size: str
    color: str
    stock_quantity: int


class ProductResponse(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str
    price_cents: int
    image_url: str
    is_featured: bool
    total_stock: int
    available_sizes: list[str]
    available_colors: list[str]
    variants: list[VariantResponse] | None = None


class OrderItemRequest(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1, le=12)


class CheckoutRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=40)
    items: list[OrderItemRequest] = Field(min_length=1)


class OrderResponse(BaseModel):
    order_id: int
    customer_id: int
    subtotal_cents: int
    items: list[dict]


@lru_cache
def database_path() -> Path:
    configured = os.getenv("STORE_DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "store.db"


def get_connection():
    connection = connect(database_path())
    try:
        yield connection
    finally:
        connection.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    connection = connect(database_path())
    try:
        initialize_database(connection)
    finally:
        connection.close()
    yield


app = FastAPI(
    title="Mom's Clothing Biz API",
    description="A portfolio-ready clothing store API using Python, explicit SQL, and tests.",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products", response_model=list[ProductResponse])
def products(
    category: str | None = None,
    size: str | None = None,
    q: str | None = Query(default=None, min_length=2),
    connection=Depends(get_connection),
):
    return list_products(connection, category=category, size=size, query=q)


@app.get("/api/products/{product_id}", response_model=ProductResponse)
def product_detail(product_id: int, connection=Depends(get_connection)):
    product = get_product(connection, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/api/filters")
def filters(connection=Depends(get_connection)) -> dict[str, list[str]]:
    return {
        "categories": list_categories(connection),
        "sizes": list_sizes(connection),
    }


@app.post("/api/orders", response_model=OrderResponse, status_code=201)
def checkout(payload: CheckoutRequest, connection=Depends(get_connection)):
    try:
        request = OrderRequest(
            email=payload.email,
            full_name=payload.full_name,
            city=payload.city,
            state=payload.state,
            items=[OrderLine(variant_id=item.variant_id, quantity=item.quantity) for item in payload.items],
        )
        return create_order(connection, request)
    except InventoryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/analytics/category-sales")
def analytics(connection=Depends(get_connection)):
    return category_sales_summary(connection)
