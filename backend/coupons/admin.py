from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "discount_type",
        "value",
        "is_active",
        "starts_at",
        "expires_at",
        "used_count",
        "usage_limit",
    ]
    list_filter = ["discount_type", "is_active", "starts_at", "expires_at"]
    search_fields = ["code"]
    readonly_fields = ["used_count", "created_at", "updated_at"]
