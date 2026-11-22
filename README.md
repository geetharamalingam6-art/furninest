# FurniNest

FurniNest is a furniture shopping application built with React/Vite and Django REST Framework.

## Current phase

The FurniNest app includes a responsive storefront, customer accounts, API-backed carts and wishlists, checkout, order history, COD/Razorpay payment flows, and a staff-only operations dashboard. Categories and product information are loaded from Django REST endpoints; no catalog products are hardcoded in React.

## Prerequisites

- Python 3.11 or newer
- Node.js 20.19 or newer and npm
- MySQL 8 for the planned database phase (SQLite is the current default for a quick local start)

## Start the backend

From the project root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

The backend health endpoint is available at `http://127.0.0.1:8000/api/health/`.
The development storefront is available at `http://localhost:5173/`.

## Catalog and storefront

- `GET /api/categories/` — active categories and their active product counts.
- `GET /api/brands/` — active brands.
- `GET /api/products/` — paginated active catalog; supports search, category/brand/material/color/price filters, and ordering.
- `GET /api/products/featured/` — paginated featured catalog.
- `GET /api/products/<slug>/` — product detail and uploaded images.

The shop and product detail pages show empty states when the database has no active catalog records. To add catalog content locally, create an admin account from the `backend` directory with `python manage.py createsuperuser`, open `http://127.0.0.1:8000/admin/`, and add categories and products. Product images can be uploaded from the product admin form.

To preview the shop with sample categories, products, and photos, run this once from the `backend` directory after migrations:

```powershell
python manage.py seed_demo_catalog
```

The demo listings are local sample data; replace their descriptions, prices, stock, and photography before using the catalog commercially.

## Customer accounts and shopping

- `POST /api/auth/register/`, `POST /api/auth/login/`, and `POST /api/auth/token/refresh/` — customer registration and JWT sessions.
- `POST /api/auth/forgot-password/` and `POST /api/auth/reset-password/` — password reset.
- `GET/PATCH /api/profile/` and `/api/addresses/` — customer profile and saved shipping addresses.
- `/api/cart/` — guest or authenticated shopping bag. Guest requests use the `X-Cart-Token` header; the frontend persists this token and merges a guest bag after sign-in.
- `/api/wishlist/` — authenticated saved products. Guest selections are stored locally and merged after sign-in.
- `GET /api/orders/checkout/summary/` — server-calculated subtotal, coupon, shipping, tax, and total.
- `POST /api/orders/checkout/` — creates an order from the signed-in customer's cart and saved address; stock changes and order snapshots are transactional.
- `GET /api/orders/` and `GET /api/orders/<id>/` — the current customer's order history and delivery status.
- `POST /api/payments/verify/` — verifies the Razorpay signature and confirms captured amount/status against Razorpay before marking an order paid.
- `/api/dashboard/overview/`, `/api/dashboard/orders/`, and `/api/dashboard/orders/<id>/status/` — staff-only order, revenue, and inventory reporting and order status management.

Cash on delivery is available without gateway credentials. To enable Razorpay, set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `backend/.env`; use Razorpay test credentials during development. Shipping and tax default to zero and can be configured with `ORDER_SHIPPING_FEE` and `ORDER_TAX_RATE_PERCENT`. Products, categories, and coupons can be managed through Django admin.

The staff dashboard is available at `/admin` in the React app after signing in with a staff account. Create a Django superuser with `python manage.py createsuperuser`; Django admin links from the dashboard open in a separate tab.

The development default is SQLite. To use MySQL, create a database and a dedicated application user using MySQL Workbench or the MySQL command line:

```sql
CREATE DATABASE furninest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'furninest_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON furninest.* TO 'furninest_app'@'localhost';
```

Edit `backend/.env` with `DB_ENGINE=mysql`, `DB_NAME=furninest`, `DB_USER=furninest_app`, your chosen `DB_PASSWORD`, `DB_HOST=127.0.0.1`, and `DB_PORT=3306`. Then run:

```powershell
python manage.py migrate
```

Never put database credentials in source code or commit your `.env` file. See [documentation/database-schema.md](./documentation/database-schema.md) for the model relationships and migration details.

## Start the frontend

In another PowerShell terminal from the project root:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`). The starter screen checks the Django health endpoint.

## Configuration and secrets

Copy the example environment files for local use. Never commit `.env` files or real Django, database, or Razorpay credentials. Set `DJANGO_DEBUG=False` and provide a strong `DJANGO_SECRET_KEY` outside local development.
