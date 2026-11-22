from rest_framework import serializers

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "sku", "quantity", "unit_price", "line_total"]

    def get_line_total(self, item):
        return item.line_total


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["previous_status", "status", "note", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_label = serializers.CharField(source="get_payment_method_display", read_only=True)
    payment_status_label = serializers.CharField(source="get_payment_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "status_label",
            "payment_method",
            "payment_method_label",
            "payment_status",
            "payment_status_label",
            "subtotal",
            "discount_amount",
            "shipping_amount",
            "tax_amount",
            "total_amount",
            "shipping_full_name",
            "shipping_phone",
            "shipping_address_line_1",
            "shipping_address_line_2",
            "shipping_city",
            "shipping_state",
            "shipping_postal_code",
            "shipping_country",
            "delivery_instructions",
            "tracking_number",
            "items",
            "status_history",
            "created_at",
            "updated_at",
        ]


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(min_value=1)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    coupon_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
