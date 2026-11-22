# FurniNest database schema

Django models are the schema source of truth. Use `python manage.py makemigrations` to generate migration files and `python manage.py migrate` to apply them; do not make ordinary application queries with handwritten SQL.

## Apps and relationships

- **accounts** — `User` authenticates by unique email; `UserProfile` extends the user profile; `Address` stores a user's saved delivery addresses.
- **products** — `Category` supports parent/child categories; `Brand` and `Category` each relate to many `Product` records; `ProductImage` stores ordered product images.
- **cart** — `Cart` belongs to one user or has a unique guest token; `CartItem` links a cart to a product with a positive quantity and a unique cart/product pair.
- **wishlist** — one `Wishlist` per user; `WishlistItem` prevents duplicate products in that list.
- **coupons** — `Coupon` stores fixed or percentage discounts, validity dates, usage counts, and limits.
- **orders** — `Order` belongs to a user and can reference a coupon; `OrderItem` snapshots product name, SKU, price, and quantity; `OrderStatusHistory` records status changes; `InventoryTransaction` records stock movements.
- **payments** — `Payment` records a provider transaction against an order, including provider identifiers, amount, status, and verification signature.
- **reviews** — `ProductReview` links a product and customer to one purchased `OrderItem`, preventing more than one review per purchased item.
- **communications** — `ContactMessage` stores customer enquiries; `NewsletterSubscriber` stores normalized unique email subscriptions.
- **dashboard** — reserved for reporting and admin-facing APIs; its statistics will query the domain models.

## Database constraints

The initial migrations include unique identifiers, relationship constraints, indexes for common catalog/order lookups, positive quantity and price checks, discount bounds, unique cart/wishlist entries, and a guest-cart ownership check. Input validation that spans multiple records (for example ensuring a review's user and product match its order item) belongs in the API/service layer and will be added with those workflows.

MySQL configuration uses the PyMySQL driver and `utf8mb4`. SQLite remains the out-of-box local default. To use MySQL, create the database and application user as described in the root [README](../README.md), then set `DB_ENGINE=mysql` and the `DB_*` values in `backend/.env` before migrating.

## Initial migration commands

Run from the `backend` directory:

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
```

The custom `accounts.User` model is configured before the initial account migrations. Do not change `AUTH_USER_MODEL` after deploying or migrating a database with user data.
