from rest_framework import serializers

from products.models import Product
from products.serializers import ProductImageSerializer

from .models import Cart, CartItem


class CartProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "discount_price",
            "current_price",
            "stock_quantity",
            "images",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "line_total"]

    def get_line_total(self, item):
        return item.product.current_price * item.quantity


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    guest_token = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "guest_token", "items", "item_count", "subtotal", "updated_at"]

    def get_guest_token(self, cart):
        request = self.context.get("request")
        if request is not None and not request.user.is_authenticated:
            return str(cart.guest_token)
        return None

    def get_item_count(self, cart):
        return sum(item.quantity for item in cart.items.all())

    def get_subtotal(self, cart):
        return sum(
            (item.product.current_price * item.quantity for item in cart.items.all()),
            start=0,
        )


class CartAddSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(is_active=True, category__is_active=True),
    )
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
