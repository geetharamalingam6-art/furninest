from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from products.models import Category, Product

from .models import Cart, CartItem


class CartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        category = Category.objects.create(name="Lounge", slug="lounge")
        self.product = Product.objects.create(
            category=category,
            name="Lounge Chair",
            slug="lounge-chair",
            sku="LOUNGE-CHAIR-01",
            description="A test chair.",
            price=Decimal("349.00"),
            stock_quantity=3,
        )

    def guest_token(self):
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, 200)
        return response.data["guest_token"]

    def test_guest_cart_token_add_update_stock_and_remove(self):
        token = self.guest_token()
        self.client.credentials(HTTP_X_CART_TOKEN=token)
        added = self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )

        self.assertEqual(added.status_code, 200)
        self.assertEqual(added.data["item_count"], 2)
        self.assertEqual(added.data["subtotal"], Decimal("698.00"))
        item_id = added.data["items"][0]["id"]

        too_many = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {"quantity": 4},
            format="json",
        )
        self.assertEqual(too_many.status_code, 400)
        self.assertEqual(CartItem.objects.get(pk=item_id).quantity, 2)

        updated = self.client.patch(
            f"/api/cart/items/{item_id}/",
            {"quantity": 3},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["item_count"], 3)

        removed = self.client.delete(f"/api/cart/items/{item_id}/")
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.data["item_count"], 0)

    def test_cart_token_is_required_to_access_the_same_guest_cart(self):
        token = self.guest_token()
        self.client.credentials(HTTP_X_CART_TOKEN="not-a-uuid")
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, 400)
        self.client.credentials(HTTP_X_CART_TOKEN=token)
        same_cart = self.client.get("/api/cart/")
        self.assertEqual(same_cart.data["guest_token"], token)

    def test_guest_cart_merges_into_authenticated_customer_cart(self):
        token = self.guest_token()
        self.client.credentials(HTTP_X_CART_TOKEN=token)
        self.client.post(
            "/api/cart/add/",
            {"product_id": self.product.id, "quantity": 2},
            format="json",
        )
        guest_cart = Cart.objects.get(guest_token=token)
        user = get_user_model().objects.create_user("cart-owner@example.com", "secure-password")
        self.client.force_authenticate(user)

        merged = self.client.get("/api/cart/")

        self.assertEqual(merged.status_code, 200)
        self.assertIsNone(merged.data["guest_token"])
        self.assertEqual(merged.data["items"][0]["quantity"], 2)
        self.assertFalse(Cart.objects.filter(pk=guest_cart.pk).exists())

