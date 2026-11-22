from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import WishlistItem


class WishlistApiTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("wishlist@example.com", "secure-password")
        category = Category.objects.create(name="Dining", slug="dining")
        self.product = Product.objects.create(
            category=category,
            name="Dining Chair",
            slug="dining-chair",
            sku="DINING-CHAIR-01",
            description="A test dining chair.",
            price=Decimal("199.00"),
            stock_quantity=2,
        )
        self.client = APIClient()
        self.client.force_authenticate(user)

    def test_add_is_idempotent_and_move_to_cart_removes_wishlist_item(self):
        first = self.client.post(
            "/api/wishlist/add/",
            {"product_id": self.product.id},
            format="json",
        )
        second = self.client.post(
            "/api/wishlist/add/",
            {"product_id": self.product.id},
            format="json",
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(WishlistItem.objects.count(), 1)

        item_id = second.data[0]["id"]
        moved = self.client.post(f"/api/wishlist/items/{item_id}/move-to-cart/")

        self.assertEqual(moved.status_code, 200)
        self.assertEqual(WishlistItem.objects.count(), 0)
        cart = self.client.get("/api/cart/")
        self.assertEqual(cart.data["item_count"], 1)
