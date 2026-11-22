from django.db import transaction
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import CartItem
from cart.views import get_cart_for_request
from products.models import Product

from .models import Wishlist, WishlistItem
from .serializers import WishlistAddSerializer, WishlistItemSerializer


def get_wishlist(user):
    wishlist, _ = Wishlist.objects.get_or_create(user=user)
    return (
        Wishlist.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=WishlistItem.objects.select_related("product").prefetch_related(
                    "product__images"
                ),
            )
        )
        .get(pk=wishlist.pk)
    )


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = get_wishlist(request.user)
        return Response(
            WishlistItemSerializer(
                wishlist.items.all(),
                many=True,
                context={"request": request},
            ).data
        )


class WishlistAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WishlistAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wishlist = get_wishlist(request.user)
        WishlistItem.objects.get_or_create(
            wishlist=wishlist,
            product=serializer.validated_data["product"],
        )
        return Response(
            WishlistItemSerializer(
                get_wishlist(request.user).items.all(),
                many=True,
                context={"request": request},
            ).data,
            status=status.HTTP_200_OK,
        )


class WishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = WishlistItem.objects.get(wishlist__user=request.user, pk=item_id)
        except WishlistItem.DoesNotExist as error:
            raise NotFound("This wishlist item does not exist.") from error
        item.delete()
        return Response(
            WishlistItemSerializer(
                get_wishlist(request.user).items.all(),
                many=True,
                context={"request": request},
            ).data
        )


class WishlistMoveToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        with transaction.atomic():
            try:
                item = WishlistItem.objects.select_for_update().select_related("product").get(
                    wishlist__user=request.user,
                    pk=item_id,
                )
            except WishlistItem.DoesNotExist as error:
                raise NotFound("This wishlist item does not exist.") from error
            product = Product.objects.select_for_update().filter(
                pk=item.product_id,
                is_active=True,
                category__is_active=True,
            ).first()
            if product is None:
                raise NotFound("This product is no longer available.")
            if product.stock_quantity < 1:
                raise ValidationError({"product": "This product is out of stock."})
            cart = get_cart_for_request(request)
            cart_item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": 1},
            )
            if not created:
                if cart_item.quantity >= product.stock_quantity:
                    raise ValidationError(
                        {"quantity": f"Only {product.stock_quantity} of this product are available."}
                    )
                cart_item.quantity += 1
                cart_item.save(update_fields=["quantity", "updated_at"])
            item.delete()
        return Response({"detail": "Product moved to cart."})
