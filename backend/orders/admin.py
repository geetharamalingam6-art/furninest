from django.contrib import admin

from .models import InventoryTransaction, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "sku", "quantity", "unit_price"]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["previous_status", "status", "note", "changed_by", "created_at"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "user",
        "status",
        "payment_method",
        "payment_status",
        "total_amount",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "payment_status", "created_at"]
    search_fields = ["order_number", "user__email", "shipping_full_name"]
    readonly_fields = [
        "order_number",
        "user",
        "subtotal",
        "discount_amount",
        "shipping_amount",
        "tax_amount",
        "total_amount",
        "created_at",
        "updated_at",
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ["product", "reason", "quantity_change", "stock_after", "created_at"]
    list_filter = ["reason", "created_at"]
    search_fields = ["product__sku", "product__name", "note"]
    readonly_fields = [
        "product",
        "order_item",
        "reason",
        "quantity_change",
        "stock_after",
        "note",
        "changed_by",
        "created_at",
    ]
