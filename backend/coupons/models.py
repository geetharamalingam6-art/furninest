from django.db import models
from django.db.models import Q
from django.utils import timezone


class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=12, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(value__gt=0), name="coupon_value_positive"),
            models.CheckConstraint(
                condition=Q(minimum_order_amount__gte=0),
                name="coupon_minimum_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(discount_type="fixed") | Q(value__lte=100),
                name="coupon_percentage_at_most_100",
            ),
            models.CheckConstraint(
                condition=Q(maximum_discount__isnull=True) | Q(maximum_discount__gte=0),
                name="coupon_max_discount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(usage_limit__isnull=True) | Q(usage_limit__gt=0),
                name="coupon_limit_positive",
            ),
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code
