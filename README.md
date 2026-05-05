# Mom's Clothing Biz

A full-stack clothing storefront built to fill the SWE I portfolio gaps recruiters often filter on:

- **Python:** FastAPI backend in `backend/app`.
- **Testing:** Python API/database tests plus React component tests.
- **Docker:** Separate backend/frontend Dockerfiles and `docker-compose.yml`.
- **TypeScript:** React + Vite + strict TypeScript frontend.
- **CI/CD:** GitHub Actions runs backend tests, frontend tests/build, and Docker builds.
- **Visible SQL:** SQLite schema, seed data, joins, `GROUP BY`, aggregation, and inventory updates are written directly in SQL.

## Features

- Product catalog with category, size, and search filters.
- Product variants with stock counts.
- Cart and checkout flow.
- Admin dashboard for updating store contact info and the storefront photo.
- Python API that persists customers, orders, and order items.
- Analytics endpoint showing revenue by category using explicit SQL joins and aggregation.

## Tech Stack

| Layer | Tools |
| --- | --- |
| Frontend | React, TypeScript, Vite, Vitest, Testing Library |
| Backend | Python, FastAPI, Pydantic, SQLite |
| Testing | Pytest, unittest, Vitest |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Run Locally

Start the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`.

## Run With Docker

```powershell
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Test Commands

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm test
npm run build
```

## SQL Talking Points

The SQL is intentionally visible in `backend/app/db.py` and `backend/app/sql/queries.sql`.

You can talk through:

- `JOIN` between `products`, `variants`, `orders`, `order_items`, and `customers`.
- `GROUP BY` and `SUM` in `category_sales_summary`.
- Parameterized filters for category, size, and search.
- Transactional checkout that inserts an order and decrements inventory.

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Health check |
| GET | `/api/products` | Product listing with optional `category`, `size`, and `q` filters |
| GET | `/api/products/{product_id}` | Product details with variants |
| GET | `/api/filters` | Available categories and sizes |
| GET | `/api/store-profile` | Editable storefront contact info and hero photo |
| PUT | `/api/admin/store-profile` | Admin update for profile/contact/photo demo |
| POST | `/api/orders` | Checkout |
| GET | `/api/analytics/category-sales` | SQL aggregation by category |
