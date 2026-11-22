from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import InventoryTransaction, Order, OrderItem, OrderStatusHistory
from payments.models import Payment
from products.models import Category, Product


class DashboardApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            "dashboard-customer@example.com",
            "secure-password",
        )
        self.admin = user_model.objects.create_user(
            "dashboard-admin@example.com",
            "secure-password",
            is_staff=True,
        )
        category = Category.objects.create(name="Office", slug="office")
        self.product = Product.objects.create(
            category=category,
            name="Desk Chair",
            slug="desk-chair",
            sku="DESK-CHAIR-01",
            description="A test office chair.",
            price=Decimal("250.00"),
            stock_quantity=3,
        )
        self.client = APIClient()

    def create_order(self, status=Order.Status.CONFIRMED):
        order = Order.objects.create(
            user=self.customer,
            status=status,
            payment_method=Order.PaymentMethod.COD,
            payment_status=Order.PaymentStatus.UNPAID,
            shipping_full_name="Dashboard Customer",
            shipping_phone="9876543210",
            shipping_address_line_1="12 Example Road",
            shipping_city="Pune",
            shipping_state="Maharashtra",
            shipping_postal_code="411001",
        )
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            quantity=2,
            unit_price=Decimal("250.00"),
        )
        order.subtotal = Decimal("500.00")
        order.total_amount = Decimal("500.00")
        order.save(update_fields=["subtotal", "total_amount"])
        return order, item

    def test_dashboard_endpoints_require_staff(self):
        self.client.force_authenticate(self.customer)

        overview = self.client.get("/api/dashboard/overview/")
        orders = self.client.get("/api/dashboard/orders/")

        self.assertEqual(overview.status_code, 403)
        self.assertEqual(orders.status_code, 403)

    def test_overview_returns_real_order_and_inventory_metrics(self):
        self.create_order()
        self.client.force_authenticate(self.admin)

        response = self.client.get("/api/dashboard/overview/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_orders"], 1)
        self.assertEqual(response.data["to_fulfill"], 1)
        self.assertEqual(response.data["low_stock_count"], 1)
        self.assertEqual(response.data["recent_orders"][0]["shipping_full_name"], "Dashboard Customer")

    def test_admin_cancellation_restores_stock_and_records_history(self):
        order, item = self.create_order()
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/dashboard/orders/{order.pk}/status/",
            {"status": Order.Status.CANCELLED, "note": "Customer requested cancellation."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(
            InventoryTransaction.objects.get(order_item=item).quantity_change,
            2,
        )
        self.assertEqual(OrderStatusHistory.objects.get(order=order).note, "Customer requested cancellation.")

    def test_cod_delivery_marks_payment_as_paid(self):
        order, _ = self.create_order(Order.Status.OUT_FOR_DELIVERY)
        payment = Payment.objects.create(
            order=order,
            provider=Payment.Provider.COD,
            amount=Decimal("500.00"),
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/dashboard/orders/{order.pk}/status/",
            {"status": Order.Status.DELIVERED},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(payment.status, Payment.Status.CAPTURED)

    def test_invalid_order_transition_is_rejected(self):
        order, _ = self.create_order()
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            f"/api/dashboard/orders/{order.pk}/status/",
            {"status": Order.Status.DELIVERED},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CONFIRMED)
