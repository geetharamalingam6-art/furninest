from django.db import models
from django.db.models import Q


class Payment(models.Model):
    class Provider(models.TextChoices):
        RAZORPAY = "razorpay", "Razorpay"
        COD = "cod", "Cash on delivery"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    provider = models.CharField(max_length=12, choices=Provider.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CREATED)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    gateway_order_id = models.CharField(max_length=100, blank=True)
    gateway_payment_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
            models.Index(fields=["provider", "gateway_order_id"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive")
        ]

    def __str__(self):
        return f"{self.provider} payment for {self.order.order_number}"
