from __future__ import annotations

import base64
import binascii
import hashlib
import os
import time
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

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
    get_product_inventory,
    get_store_profile,
    initialize_database,
    list_categories,
    list_model_shots,
    list_product_inventory,
    list_products,
    list_sizes,
    update_store_profile,
)
from app.fashn import FashnError, generate_fashn_model_shot, is_fashn_configured


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


class StoreProfileResponse(BaseModel):
    id: int
    business_name: str
    tagline: str
    contact_name: str
    email: EmailStr
    phone: str
    city: str
    state: str
    instagram_url: str
    hero_image_url: str
    updated_at: str


class StoreProfileRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=80)
    tagline: str = Field(min_length=8, max_length=180)
    contact_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=32)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=24)
    instagram_url: str = Field(min_length=8, max_length=220)
    hero_image_url: str = Field(min_length=8, max_length=500)
    hero_image_data_url: str | None = None


class QualityProfileResponse(BaseModel):
    quality_tier: str
    quality_label: str
    generation_mode: str
    notes: str


class ProductInventoryResponse(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    image_url: str
    price_cents: int
    total_stock: int
    quality_profile: QualityProfileResponse


class ModelShotRequestBody(BaseModel):
    product_id: int
    source_image_url: str | None = Field(default=None, max_length=500)
    source_image_data_url: str | None = None


class ModelShotResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    category: str
    source_image_url: str
    generated_image_url: str
    quality_tier: str
    quality_label: str
    generation_mode: str
    stock_quantity: int
    status: str
    notes: str
    created_at: str


@lru_cache
def database_path() -> Path:
    configured = os.getenv("STORE_DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "store.db"


@lru_cache
def uploads_path() -> Path:
    return database_path().parent / "uploads"


def get_connection():
    connection = connect(database_path())
    try:
        yield connection
    finally:
        connection.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    uploads_path().mkdir(parents=True, exist_ok=True)
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

app.mount("/uploads", StaticFiles(directory=str(uploads_path()), check_dir=False), name="uploads")


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


@app.get("/api/store-profile", response_model=StoreProfileResponse)
def store_profile(connection=Depends(get_connection)):
    return get_store_profile(connection)


@app.put("/api/admin/store-profile", response_model=StoreProfileResponse)
def admin_update_store_profile(payload: StoreProfileRequest, connection=Depends(get_connection)):
    hero_image_url = payload.hero_image_url
    if payload.hero_image_data_url:
        hero_image_url = _save_upload(payload.hero_image_data_url, prefix="profile")

    profile = StoreProfileUpdate(
        business_name=payload.business_name,
        tagline=payload.tagline,
        contact_name=payload.contact_name,
        email=payload.email,
        phone=payload.phone,
        city=payload.city,
        state=payload.state,
        instagram_url=payload.instagram_url,
        hero_image_url=hero_image_url,
    )
    return update_store_profile(connection, profile)


@app.get("/api/admin/products/inventory", response_model=list[ProductInventoryResponse])
def admin_product_inventory(connection=Depends(get_connection)):
    return list_product_inventory(connection)


@app.get("/api/admin/model-shots", response_model=list[ModelShotResponse])
def admin_model_shots(connection=Depends(get_connection)):
    return list_model_shots(connection)


@app.post("/api/admin/model-shots", response_model=ModelShotResponse, status_code=201)
def admin_create_model_shot(payload: ModelShotRequestBody, connection=Depends(get_connection)):
    product = get_product_inventory(connection, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {payload.product_id} does not exist.")

    source_image_url = payload.source_image_url or product["image_url"]
    provider_image = payload.source_image_data_url or source_image_url
    if payload.source_image_data_url:
        source_image_url = _save_upload(payload.source_image_data_url, prefix="garment")

    generated_image_url = None
    generation_mode = None
    notes = None
    quality_profile = product["quality_profile"]

    if is_fashn_configured():
        try:
            generated = generate_fashn_model_shot(
                garment_image=provider_image,
                quality_profile=quality_profile,
                product_category=product["category"],
            )
        except FashnError as exc:
            if not _allow_fashn_demo_fallback():
                raise HTTPException(status_code=502, detail=str(exc)) from exc
        else:
            generated_image_url = generated.generated_image_url
            generation_mode = generated.generation_mode
            notes = (
                f"FASHN {generated.model_name} completed with prediction "
                f"{generated.prediction_id}. {quality_profile['notes']}"
            )

    return create_model_shot(
        connection,
        ModelShotRequest(
            product_id=payload.product_id,
            source_image_url=source_image_url,
            generated_image_url=generated_image_url,
            generation_mode=generation_mode,
            notes=notes,
        ),
    )


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


def _save_upload(data_url: str, *, prefix: str) -> str:
    accepted_types = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    header, separator, encoded = data_url.partition(",")
    if not separator or not header.startswith("data:") or ";base64" not in header:
        raise HTTPException(status_code=400, detail="Image must be a base64 data URL.")

    content_type = header.removeprefix("data:").split(";", 1)[0]
    extension = accepted_types.get(content_type)
    if extension is None:
        raise HTTPException(status_code=400, detail="Use a JPG, PNG, or WebP image.")

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Image data is not valid base64.") from exc

    if len(image_bytes) > 8_000_000:
        raise HTTPException(status_code=413, detail="Image must be smaller than 8 MB.")

    digest = hashlib.sha256(image_bytes).hexdigest()[:12]
    filename = f"{prefix}-{int(time.time())}-{digest}.{extension}"
    uploads_path().mkdir(parents=True, exist_ok=True)
    (uploads_path() / filename).write_bytes(image_bytes)
    return f"/uploads/{filename}"


def _allow_fashn_demo_fallback() -> bool:
    return os.getenv("FASHN_ALLOW_DEMO_FALLBACK", "").lower() in {"1", "true", "yes"}
