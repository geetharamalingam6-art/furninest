import uuid

from django.db import transaction
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import Product

from .models import Cart, CartItem
from .serializers import CartAddSerializer, CartItemUpdateSerializer, CartSerializer


def cart_query():
    return Cart.objects.prefetch_related(
        Prefetch(
            "items",
            queryset=CartItem.objects.select_related("product").prefetch_related("product__images"),
        )
    )


def get_cart_for_request(request):
    raw_token = request.headers.get("X-Cart-Token")
    guest_cart = None
    if raw_token:
        try:
            token = uuid.UUID(raw_token)
        except (ValueError, TypeError, AttributeError) as error:
            raise ValidationError({"cart_token": "The guest cart token is invalid."}) from error
        guest_cart = Cart.objects.filter(guest_token=token, user__isnull=True).first()

    if request.user.is_authenticated:
        with transaction.atomic():
            cart, _ = Cart.objects.select_for_update().get_or_create(user=request.user)
            if guest_cart is not None and guest_cart.pk != cart.pk:
                guest_cart = Cart.objects.select_for_update().get(pk=guest_cart.pk)
                for guest_item in guest_cart.items.select_for_update().select_related("product"):
                    product = Product.objects.select_for_update().filter(
                        pk=guest_item.product_id,
                        is_active=True,
                        category__is_active=True,
                    ).first()
                    if product is None or product.stock_quantity < 1:
                        continue
                    item, created = CartItem.objects.select_for_update().get_or_create(
                        cart=cart,
                        product=product,
                        defaults={"quantity": min(guest_item.quantity, product.stock_quantity)},
                    )
                    if not created:
                        item.quantity = min(
                            item.quantity + guest_item.quantity,
                            product.stock_quantity,
                        )
                        item.save(update_fields=["quantity", "updated_at"])
                guest_cart.delete()
        return cart_query().get(pk=cart.pk)

    if guest_cart is not None:
        return cart_query().get(pk=guest_cart.pk)
    cart = Cart.objects.create()
    return cart_query().get(pk=cart.pk)


def get_owned_item(cart, item_id):
    try:
        return CartItem.objects.select_related("product").get(cart=cart, pk=item_id)
    except CartItem.DoesNotExist as error:
        raise NotFound("This cart item does not exist.") from error


class CartView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_cart_for_request(request)
        return Response(CartSerializer(cart, context={"request": request}).data)


class CartAddView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            cart = get_cart_for_request(request)
            product = Product.objects.select_for_update().get(
                pk=serializer.validated_data["product"].pk,
                is_active=True,
                category__is_active=True,
            )
            quantity = serializer.validated_data["quantity"]
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart,
                product=product,
                defaults={"quantity": quantity},
            )
            requested_quantity = quantity if created else item.quantity + quantity
            if requested_quantity > product.stock_quantity:
                raise ValidationError(
                    {"quantity": f"Only {product.stock_quantity} of this product are available."}
                )
            if not created:
                item.quantity = requested_quantity
                item.save(update_fields=["quantity", "updated_at"])
            cart = cart_query().get(pk=cart.pk)
        return Response(
            CartSerializer(cart, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )


class CartItemView(APIView):
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            cart = get_cart_for_request(request)
            item = get_owned_item(cart, item_id)
            product = Product.objects.select_for_update().get(pk=item.product_id)
            quantity = serializer.validated_data["quantity"]
            if quantity > product.stock_quantity:
                raise ValidationError(
                    {"quantity": f"Only {product.stock_quantity} of this product are available."}
                )
            item.quantity = quantity
            item.save(update_fields=["quantity", "updated_at"])
            cart = cart_query().get(pk=cart.pk)
        return Response(CartSerializer(cart, context={"request": request}).data)

    def delete(self, request, item_id):
        with transaction.atomic():
            cart = get_cart_for_request(request)
            get_owned_item(cart, item_id).delete()
            cart = cart_query().get(pk=cart.pk)
        return Response(CartSerializer(cart, context={"request": request}).data)


class CartClearView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_cart_for_request(request)
        cart.items.all().delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart, context={"request": request}).data)
