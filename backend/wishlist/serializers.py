from rest_framework import serializers

from cart.serializers import CartProductSerializer
from products.models import Product

from .models import WishlistItem


class WishlistItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ["id", "product", "created_at"]


class WishlistAddSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.filter(is_active=True, category__is_active=True),
    )
