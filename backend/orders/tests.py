from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
import uuid
from rest_framework.test import APIClient

from accounts.models import Address
from cart.models import Cart, CartItem
from coupons.models import Coupon
from orders.models import InventoryTransaction, Order, OrderEmailEvent
from payments.models import Payment
from payments.services import RazorpayError
from products.models import Category, Product


@override_settings(
    ORDER_SHIPPING_FEE=Decimal("10.00"),
    ORDER_TAX_RATE_PERCENT=Decimal("10"),
    RAZORPAY_KEY_ID="rzp_test_key",
    RAZORPAY_KEY_SECRET="test_secret",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class CheckoutApiTests(TestCase):
    def setUp(self):
        mail.outbox.clear()
        self.user = get_user_model().objects.create_user(
            "checkout@example.com",
            "secure-password",
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name="Checkout Customer",
            phone_number="9876543210",
            address_line_1="12 Example Road",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
            country="India",
        )
        category = Category.objects.create(name="Living", slug="living")
        self.product = Product.objects.create(
            category=category,
            name="Armchair",
            slug="armchair",
            sku="ARMCHAIR-01",
            description="A test armchair.",
            price=Decimal("200.00"),
            stock_quantity=5,
        )
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=2,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {
            "address_id": self.address.pk,
            "payment_method": Order.PaymentMethod.COD,
        }

    def test_order_status_emails_are_sent_once_after_confirmed_transitions(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/orders/checkout/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(pk=response.data["id"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.order_number, mail.outbox[0].subject)

        with self.captureOnCommitCallbacks(execute=True):
            order.status = Order.Status.SHIPPED
            order.tracking_number = "TRACK-123"
            order.save()
            order.save()
            order.status = Order.Status.DELIVERED
            order.save()
            order.payment_status = Order.PaymentStatus.PAID
            order.save()
            order.payment_status = Order.PaymentStatus.REFUNDED
            order.save()

        events = set(OrderEmailEvent.objects.filter(order=order).values_list("event", flat=True))
        self.assertEqual(events, {
            OrderEmailEvent.Event.CONFIRMATION,
            OrderEmailEvent.Event.SHIPPED,
            OrderEmailEvent.Event.DELIVERED,
            OrderEmailEvent.Event.PAYMENT,
            OrderEmailEvent.Event.REFUND,
        })
        self.assertEqual(len(mail.outbox), 5)
        self.assertIn("TRACK-123", mail.outbox[1].body)

    def test_cod_checkout_calculates_total_and_records_stock_history(self):
        response = self.client.post("/api/orders/checkout/", self.payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("400.00"))
        self.assertEqual(Decimal(response.data["shipping_amount"]), Decimal("10.00"))
        self.assertEqual(Decimal(response.data["tax_amount"]), Decimal("40.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("450.00"))
        self.assertEqual(response.data["status"], Order.Status.CONFIRMED)
        self.assertEqual(response.data["payment_status"], Order.PaymentStatus.UNPAID)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertFalse(CartItem.objects.filter(pk=self.cart_item.pk).exists())
        self.assertEqual(
            InventoryTransaction.objects.get().quantity_change,
            -2,
        )
        self.assertEqual(Payment.objects.get().provider, Payment.Provider.COD)

    def test_invalid_coupon_leaves_cart_and_stock_unchanged(self):
        response = self.client.post(
            "/api/orders/checkout/",
            {**self.payload, "coupon_code": "NOT-REAL"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
        self.assertTrue(CartItem.objects.filter(pk=self.cart_item.pk).exists())

    def test_out_of_stock_product_cannot_be_ordered(self):
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])

        response = self.client.post("/api/orders/checkout/", self.payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.assertTrue(CartItem.objects.filter(pk=self.cart_item.pk).exists())

    def test_checkout_rejects_an_address_owned_by_another_customer(self):
        other_user = get_user_model().objects.create_user(
            "other-checkout@example.com",
            "secure-password",
        )
        other_address = Address.objects.create(
            user=other_user,
            full_name="Other Customer",
            phone_number="9876543210",
            address_line_1="1 Private Road",
            city="Pune",
            state="Maharashtra",
            postal_code="411001",
        )

        response = self.client.post(
            "/api/orders/checkout/",
            {**self.payload, "address_id": other_address.pk},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_coupon_discount_and_usage_are_applied_atomically(self):
        coupon = Coupon.objects.create(
            code="SAVE50",
            discount_type=Coupon.DiscountType.FIXED,
            value=Decimal("50.00"),
            minimum_order_amount=Decimal("300.00"),
            expires_at=timezone.now() + timedelta(days=1),
            usage_limit=1,
        )

        response = self.client.post(
            "/api/orders/checkout/",
            {**self.payload, "coupon_code": "save50"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Decimal(response.data["discount_amount"]), Decimal("50.00"))
        self.assertEqual(Decimal(response.data["tax_amount"]), Decimal("35.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("395.00"))
        coupon.refresh_from_db()
        self.assertEqual(coupon.used_count, 1)

    def test_checkout_summary_uses_server_configured_totals_and_coupon(self):
        Coupon.objects.create(
            code="SAVE50",
            discount_type=Coupon.DiscountType.FIXED,
            value=Decimal("50.00"),
            minimum_order_amount=Decimal("300.00"),
            expires_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(
            "/api/orders/checkout/summary/",
            {"coupon_code": "save50"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("400.00"))
        self.assertEqual(Decimal(response.data["discount_amount"]), Decimal("50.00"))
        self.assertEqual(Decimal(response.data["shipping_amount"]), Decimal("10.00"))
        self.assertEqual(Decimal(response.data["tax_amount"]), Decimal("35.00"))
        self.assertEqual(Decimal(response.data["total_amount"]), Decimal("395.00"))
        self.assertEqual(response.data["coupon_code"], "SAVE50")

    def test_razorpay_checkout_creates_server_amount_and_verifies_capture(self):
        checkout_payload = {
            **self.payload,
            "payment_method": Order.PaymentMethod.RAZORPAY,
        }
        with patch(
            "orders.views.create_razorpay_order",
            return_value={"id": "order_gateway_123"},
        ) as create_gateway_order:
            response = self.client.post(
                "/api/orders/checkout/",
                checkout_payload,
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        create_gateway_order.assert_called_once_with(
            amount_paise=45_000,
            receipt=response.data["order"]["order_number"],
            notes={"order_number": response.data["order"]["order_number"]},
        )
        payment = Payment.objects.get()
        self.assertEqual(payment.amount, Decimal("450.00"))
        self.assertEqual(payment.gateway_order_id, "order_gateway_123")

        import hashlib
        import hmac

        payment_id = "pay_gateway_123"
        signature = hmac.new(
            b"test_secret",
            f"{payment.gateway_order_id}|{payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        with patch(
            "payments.views.fetch_razorpay_payment",
            return_value={
                "order_id": payment.gateway_order_id,
                "amount": 45_000,
                "currency": "INR",
                "status": "captured",
            },
        ):
            verified = self.client.post(
                "/api/payments/verify/",
                {
                    "order_id": response.data["order"]["id"],
                    "razorpay_order_id": payment.gateway_order_id,
                    "razorpay_payment_id": payment_id,
                    "razorpay_signature": signature,
                },
                format="json",
            )

        self.assertEqual(verified.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CAPTURED)
        order = Order.objects.get(pk=response.data["order"]["id"])
        self.assertEqual(order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(order.status, Order.Status.CONFIRMED)
        self.assertFalse(CartItem.objects.filter(pk=self.cart_item.pk).exists())

    def test_razorpay_checkout_is_idempotent_for_the_same_request_key(self):
        checkout_payload = {
            **self.payload,
            "payment_method": Order.PaymentMethod.RAZORPAY,
        }
        key = str(uuid.uuid4())
        with patch(
            "orders.views.create_razorpay_order",
            return_value={"id": "order_gateway_idempotent"},
        ) as create_gateway_order:
            first = self.client.post(
                "/api/orders/checkout/",
                checkout_payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )
            second = self.client.post(
                "/api/orders/checkout/",
                checkout_payload,
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
            )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.data["order"]["id"], second.data["order"]["id"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Payment.objects.count(), 1)
        create_gateway_order.assert_called_once()

    @override_settings(RAZORPAY_KEY_ID="rzp_live_not_allowed")
    def test_online_checkout_requires_razorpay_test_credentials(self):
        summary = self.client.get("/api/orders/checkout/summary/")
        self.assertFalse(summary.data["razorpay_enabled"])
        response = self.client.post(
            "/api/orders/checkout/",
            {**self.payload, "payment_method": Order.PaymentMethod.RAZORPAY},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Order.objects.exists())

    def test_invalid_razorpay_signature_is_rejected_without_gateway_lookup(self):
        checkout_payload = {
            **self.payload,
            "payment_method": Order.PaymentMethod.RAZORPAY,
        }
        with patch(
            "orders.views.create_razorpay_order",
            return_value={"id": "order_gateway_123"},
        ):
            checkout = self.client.post(
                "/api/orders/checkout/",
                checkout_payload,
                format="json",
            )
        payment = Payment.objects.get()
        with patch("payments.views.fetch_razorpay_payment") as fetch_payment:
            response = self.client.post(
                "/api/payments/verify/",
                {
                    "order_id": checkout.data["order"]["id"],
                    "razorpay_order_id": payment.gateway_order_id,
                    "razorpay_payment_id": "pay_gateway_123",
                    "razorpay_signature": "not-a-valid-signature",
                },
                format="json",
            )

        self.assertEqual(response.status_code, 400)
        fetch_payment.assert_not_called()
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CREATED)

    def test_order_detail_is_private_to_the_customer(self):
        checkout = self.client.post("/api/orders/checkout/", self.payload, format="json")
        other_user = get_user_model().objects.create_user(
            "private-order@example.com",
            "secure-password",
        )
        self.client.force_authenticate(other_user)

        detail = self.client.get(f"/api/orders/{checkout.data['id']}/")
        listing = self.client.get("/api/orders/")

        self.assertEqual(detail.status_code, 404)
        self.assertEqual(listing.data, [])

    def test_gateway_setup_failure_releases_stock_and_keeps_cart(self):
        checkout_payload = {
            **self.payload,
            "payment_method": Order.PaymentMethod.RAZORPAY,
        }
        with patch(
            "orders.views.create_razorpay_order",
            side_effect=RazorpayError("gateway unavailable"),
        ):
            response = self.client.post(
                "/api/orders/checkout/",
                checkout_payload,
                format="json",
            )

        self.assertEqual(response.status_code, 502)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
        self.assertTrue(CartItem.objects.filter(pk=self.cart_item.pk).exists())
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment_status, Order.PaymentStatus.FAILED)
        self.assertEqual(
            sum(tx.quantity_change for tx in InventoryTransaction.objects.all()),
            0,
        )
