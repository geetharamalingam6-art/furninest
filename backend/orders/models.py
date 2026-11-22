import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


def generate_order_number():
    return f"FN-{uuid.uuid4().hex[:12].upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on delivery"
        RAZORPAY = "razorpay", "Razorpay"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(
        max_length=15,
        unique=True,
        default=generate_order_number,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(
        max_length=12,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    payment_status = models.CharField(
        max_length=12,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    coupon = models.ForeignKey(
        "coupons.Coupon",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_full_name = models.CharField(max_length=160)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line_1 = models.CharField(max_length=255)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default="India")
    delivery_instructions = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    checkout_key = models.CharField(max_length=64, null=True, blank=True)
    checkout_fingerprint = models.CharField(max_length=64, blank=True, default="")
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["payment_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "checkout_key"],
                name="unique_user_checkout_key",
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="order_subtotal_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount_amount__gte=0),
                name="order_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(shipping_amount__gte=0),
                name="order_shipping_nonnegative",
            ),
            models.CheckConstraint(condition=Q(tax_amount__gte=0), name="order_tax_nonnegative"),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0),
                name="order_total_nonnegative",
            ),
        ]

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="order_item_quantity_positive",
            ),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0),
                name="order_item_price_nonnegative",
            ),
        ]

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.order.order_number}: {self.status}"


class OrderEmailEvent(models.Model):
    class Event(models.TextChoices):
        CONFIRMATION = "confirmation", "Order confirmation"
        PAYMENT = "payment", "Payment confirmation"
        SHIPPED = "shipped", "Order shipped"
        DELIVERED = "delivered", "Order delivered"
        CANCELLED = "cancelled", "Order cancelled"
        REFUND = "refund", "Refund confirmation"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="email_events")
    event = models.CharField(max_length=20, choices=Event.choices)
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order", "event"], name="unique_order_email_event")]


class InventoryTransaction(models.Model):
    class Reason(models.TextChoices):
        RESTOCK = "restock", "Restock"
        ORDER = "order", "Order"
        CANCELLATION = "cancellation", "Order cancellation"
        RETURN = "return", "Return"
        ADJUSTMENT = "adjustment", "Manual adjustment"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="inventory_transactions",
    )
    order_item = models.ForeignKey(
        OrderItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    quantity_change = models.IntegerField()
    stock_after = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inventory_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=~Q(quantity_change=0),
                name="inventory_quantity_change_nonzero",
            )
        ]

    def __str__(self):
        return f"{self.product.sku}: {self.quantity_change:+d}"
