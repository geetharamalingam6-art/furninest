from decimal import Decimal
from io import StringIO

from django.db import IntegrityError, transaction
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Category, Product, ProductImage


class ProductConstraintTests(TestCase):
    def test_database_rejects_nonpositive_product_price(self):
        category = Category.objects.create(name="Seating", slug="seating")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    category=category,
                    name="Invalid chair",
                    slug="invalid-chair",
                    sku="CHAIR-INVALID",
                    description="Test product",
                    price=Decimal("0.00"),
                )


class PublicCatalogApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name="Living Room",
            slug="living-room",
        )
        self.product = Product.objects.create(
            category=self.category,
            name="Oak Lounge Chair",
            slug="oak-lounge-chair",
            sku="CHAIR-OAK-01",
            description="A solid oak lounge chair.",
            price=Decimal("349.00"),
            stock_quantity=4,
            is_featured=True,
        )

    def test_catalog_lists_database_products_and_filters_by_category(self):
        response = self.client.get("/api/products/", {"category__slug": "living-room"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.product.slug)
        self.assertEqual(response.data["results"][0]["current_price"], "349.00")

    def test_featured_endpoint_and_slug_detail_use_database_records(self):
        featured = self.client.get("/api/products/featured/")
        detail = self.client.get(f"/api/products/{self.product.slug}/")

        self.assertEqual(featured.status_code, 200)
        self.assertEqual(featured.data["results"][0]["id"], self.product.id)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.data["name"], self.product.name)

    def test_categories_include_active_product_counts(self):
        response = self.client.get("/api/categories/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["product_count"], 1)


class DemoCatalogCommandTests(TestCase):
    def test_seed_command_creates_products_with_images_and_is_idempotent(self):
        call_command("seed_demo_catalog", stdout=StringIO())
        first_product_count = Product.objects.count()

        call_command("seed_demo_catalog", stdout=StringIO())

        self.assertEqual(first_product_count, 72)
        self.assertEqual(Product.objects.count(), 72)
        self.assertEqual(ProductImage.objects.count(), 72)
        self.assertEqual(Category.objects.count(), 8)
        self.assertTrue(
            ProductImage.objects.filter(image="products/demo/maison-accent-chair.jpg").exists()
        )
        self.assertTrue(
            ProductImage.objects.filter(product__category__slug="bedroom").exists()
        )
