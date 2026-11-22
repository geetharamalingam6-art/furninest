from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "provider", "status", "amount", "gateway_payment_id", "created_at"]
    list_filter = ["provider", "status", "created_at"]
    search_fields = ["order__order_number", "gateway_order_id", "gateway_payment_id"]
    readonly_fields = [
        "order",
        "provider",
        "status",
        "amount",
        "currency",
        "gateway_order_id",
        "gateway_payment_id",
        "gateway_signature",
        "failure_reason",
        "created_at",
        "updated_at",
    ]
