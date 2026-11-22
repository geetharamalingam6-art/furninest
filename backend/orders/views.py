import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Address
from cart.models import Cart, CartItem
from coupons.models import Coupon
from payments.models import Payment
from payments.services import RazorpayError, create_razorpay_order, razorpay_is_configured
from products.models import Product

from .models import InventoryTransaction, Order, OrderItem, OrderStatusHistory
from .serializers import CheckoutSerializer, OrderSerializer

CENT = Decimal("0.01")


class PaymentGatewayError(APIException):
    status_code = 502
    default_detail = "Online payment could not be started. Please try again."
    default_code = "payment_gateway_error"


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def order_query():
    return Order.objects.prefetch_related("items", "status_history")


def calculate_discount(coupon, subtotal):
    if coupon.discount_type == Coupon.DiscountType.PERCENTAGE:
        discount = subtotal * coupon.value / Decimal("100")
    else:
        discount = coupon.value
    if coupon.maximum_discount is not None:
        discount = min(discount, coupon.maximum_discount)
    return money(min(discount, subtotal))


def get_coupon(code, subtotal, lock=False):
    if not code.strip():
        return None, Decimal("0.00")
    now = timezone.now()
    coupons = Coupon.objects.select_for_update() if lock else Coupon.objects
    coupon = coupons.filter(
        code__iexact=code.strip(),
        is_active=True,
        starts_at__lte=now,
        expires_at__gte=now,
    ).first()
    if coupon is None:
        raise ValidationError({"coupon_code": "This coupon is invalid or has expired."})
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError({"coupon_code": "This coupon has reached its usage limit."})
    if subtotal < coupon.minimum_order_amount:
        raise ValidationError(
            {"coupon_code": f"Spend at least ₹{coupon.minimum_order_amount} to use this coupon."}
        )
    return coupon, calculate_discount(coupon, subtotal)


def create_order_for_user(user, checkout_data, checkout_key=None):
    payment_method = checkout_data["payment_method"]
    checkout_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "address_id": checkout_data["address_id"],
                "payment_method": payment_method,
                "coupon_code": checkout_data.get("coupon_code", "").strip().upper(),
                "delivery_instructions": checkout_data.get("delivery_instructions", ""),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    if payment_method == Order.PaymentMethod.RAZORPAY:
        if not razorpay_is_configured():
            raise ValidationError(
                {"payment_method": "Razorpay test credentials are not configured. Choose cash on delivery."}
            )

    with transaction.atomic():
        if checkout_key:
            existing_order = (
                Order.objects.select_for_update()
                .filter(user=user, checkout_key=checkout_key)
                .first()
            )
            if existing_order:
                if existing_order.checkout_fingerprint != checkout_fingerprint:
                    raise ValidationError(
                        {"detail": "This checkout request key was already used with different details."}
                    )
                payment = existing_order.payments.first()
                return order_query().get(pk=existing_order.pk), payment

        cart = Cart.objects.select_for_update().filter(user=user).first()
        if cart is None:
            raise ValidationError({"cart": "Your shopping bag is empty."})
        cart_items = list(
            CartItem.objects.select_for_update()
            .filter(cart=cart)
            .select_related("product")
            .order_by("product_id")
        )
        if not cart_items:
            raise ValidationError({"cart": "Your shopping bag is empty."})

        address = Address.objects.filter(pk=checkout_data["address_id"], user=user).first()
        if address is None:
            raise ValidationError({"address_id": "Choose one of your saved addresses."})

        product_ids = [item.product_id for item in cart_items]
        products = {
            product.pk: product
            for product in Product.objects.select_for_update()
            .filter(
                pk__in=product_ids,
                is_active=True,
                category__is_active=True,
            )
            .order_by("pk")
        }
        if len(products) != len(product_ids):
            raise ValidationError({"cart": "A product in your bag is no longer available."})
        for item in cart_items:
            product = products[item.product_id]
            if item.quantity > product.stock_quantity:
                raise ValidationError(
                    {"cart": f"Only {product.stock_quantity} of {product.name} are available."}
                )

        subtotal = money(
            sum(
                (products[item.product_id].current_price * item.quantity for item in cart_items),
                start=Decimal("0.00"),
            )
        )
        coupon, discount = get_coupon(
            checkout_data.get("coupon_code", ""),
            subtotal,
            lock=True,
        )
        shipping = money(settings.ORDER_SHIPPING_FEE)
        taxable_amount = max(Decimal("0.00"), subtotal - discount)
        tax = money(taxable_amount * settings.ORDER_TAX_RATE_PERCENT / Decimal("100"))
        total = money(taxable_amount + shipping + tax)
        if payment_method == Order.PaymentMethod.RAZORPAY and total <= 0:
            raise ValidationError({"payment_method": "Online payment requires an order total above ₹0."})

        order_status = (
            Order.Status.PENDING
            if payment_method == Order.PaymentMethod.RAZORPAY
            else Order.Status.CONFIRMED
        )
        payment_status = (
            Order.PaymentStatus.PENDING
            if payment_method == Order.PaymentMethod.RAZORPAY
            else (
                Order.PaymentStatus.PAID
                if total == 0
                else Order.PaymentStatus.UNPAID
            )
        )
        order = Order.objects.create(
            user=user,
            status=order_status,
            payment_method=payment_method,
            payment_status=payment_status,
            coupon=coupon,
            subtotal=subtotal,
            discount_amount=discount,
            shipping_amount=shipping,
            tax_amount=tax,
            total_amount=total,
            shipping_full_name=address.full_name,
            shipping_phone=address.phone_number,
            shipping_address_line_1=address.address_line_1,
            shipping_address_line_2=address.address_line_2,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,
            delivery_instructions=checkout_data.get(
                "delivery_instructions",
                address.delivery_instructions,
            ),
            checkout_key=checkout_key,
            checkout_fingerprint=checkout_fingerprint,
        )
        OrderStatusHistory.objects.create(
            order=order,
            previous_status="",
            status=order.status,
            note="Order placed.",
            changed_by=user,
        )
        for cart_item in cart_items:
            product = products[cart_item.product_id]
            product.stock_quantity -= cart_item.quantity
            product.save(update_fields=["stock_quantity", "updated_at"])
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                sku=product.sku,
                quantity=cart_item.quantity,
                unit_price=product.current_price,
            )
            InventoryTransaction.objects.create(
                product=product,
                order_item=order_item,
                reason=InventoryTransaction.Reason.ORDER,
                quantity_change=-cart_item.quantity,
                stock_after=product.stock_quantity,
                note=f"Reserved for {order.order_number}.",
                changed_by=user,
            )
        if coupon is not None:
            coupon.used_count += 1
            coupon.save(update_fields=["used_count", "updated_at"])
        payment = None
        if total > 0:
            provider = (
                Payment.Provider.RAZORPAY
                if payment_method == Order.PaymentMethod.RAZORPAY
                else Payment.Provider.COD
            )
            payment = Payment.objects.create(order=order, provider=provider, amount=total)
        if payment_method == Order.PaymentMethod.COD:
            CartItem.objects.filter(pk__in=[item.pk for item in cart_items]).delete()

    return order_query().get(pk=order.pk), payment


def release_order_stock(order):
    for item in order.items.select_related("product").select_for_update():
        product = Product.objects.select_for_update().get(pk=item.product_id)
        product.stock_quantity += item.quantity
        product.save(update_fields=["stock_quantity", "updated_at"])
        InventoryTransaction.objects.create(
            product=product,
            order_item=item,
            reason=InventoryTransaction.Reason.CANCELLATION,
            quantity_change=item.quantity,
            stock_after=product.stock_quantity,
            note=f"Released after payment setup failed for {order.order_number}.",
        )


def cancel_after_gateway_error(order_id):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.PENDING:
            return
        release_order_stock(order)
        payment = order.payments.select_for_update().first()
        if payment is not None:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = "Razorpay order creation failed."
            payment.save(update_fields=["status", "failure_reason", "updated_at"])
        order.status = Order.Status.CANCELLED
        order.payment_status = Order.PaymentStatus.FAILED
        order.checkout_key = None
        order.cancelled_at = timezone.now()
        order.save(update_fields=["status", "payment_status", "cancelled_at", "checkout_key", "updated_at"])
        OrderStatusHistory.objects.create(
            order=order,
            previous_status=Order.Status.PENDING,
            status=Order.Status.CANCELLED,
            note="Online payment could not be started.",
        )
        if order.coupon_id is not None:
            Coupon.objects.filter(pk=order.coupon_id, used_count__gt=0).update(
                used_count=models.F("used_count") - 1
            )


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = order_query().filter(user=request.user)
        return Response(OrderSerializer(orders, many=True).data)


class CheckoutSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if cart is None:
            raise ValidationError({"cart": "Your shopping bag is empty."})
        items = list(
            CartItem.objects.filter(cart=cart)
            .select_related("product")
            .order_by("product_id")
        )
        if not items:
            raise ValidationError({"cart": "Your shopping bag is empty."})
        if any(not item.product.is_active or not item.product.category.is_active for item in items):
            raise ValidationError({"cart": "A product in your bag is no longer available."})
        subtotal = money(
            sum(
                (item.product.current_price * item.quantity for item in items),
                start=Decimal("0.00"),
            )
        )
        coupon, discount = get_coupon(request.query_params.get("coupon_code", ""), subtotal)
        shipping = money(settings.ORDER_SHIPPING_FEE)
        taxable_amount = max(Decimal("0.00"), subtotal - discount)
        tax = money(taxable_amount * settings.ORDER_TAX_RATE_PERCENT / Decimal("100"))
        return Response(
            {
                "subtotal": subtotal,
                "discount_amount": discount,
                "coupon_code": coupon.code if coupon else "",
                "shipping_amount": shipping,
                "tax_amount": tax,
                "total_amount": money(taxable_amount + shipping + tax),
                "razorpay_enabled": bool(
                    razorpay_is_configured()
                ),
            }
        )


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        order = order_query().filter(user=request.user, pk=order_id).first()
        if order is None:
            raise NotFound("This order does not exist.")
        return Response(OrderSerializer(order).data)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_checkout_key = request.headers.get("Idempotency-Key", "").strip()
        try:
            checkout_key = str(UUID(raw_checkout_key)) if raw_checkout_key else None
        except ValueError as error:
            raise ValidationError({"detail": "The checkout request key is invalid."}) from error
        order, payment = create_order_for_user(
            request.user,
            serializer.validated_data,
            checkout_key=checkout_key,
        )
        if order.payment_method == Order.PaymentMethod.COD:
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        if payment.gateway_order_id:
            gateway_order_id = payment.gateway_order_id
        else:
            try:
                gateway_order = create_razorpay_order(
                    amount_paise=int(order.total_amount * 100),
                    receipt=order.order_number,
                    notes={"order_number": order.order_number},
                )
            except RazorpayError as error:
                cancel_after_gateway_error(order.pk)
                raise PaymentGatewayError(
                    "Online payment could not be started. Your bag is unchanged."
                ) from error
            gateway_order_id = gateway_order["id"]
            payment.gateway_order_id = gateway_order_id
            payment.save(update_fields=["gateway_order_id", "updated_at"])
        return Response(
            {
                "order": OrderSerializer(order).data,
                "payment": {
                    "key_id": settings.RAZORPAY_KEY_ID,
                    "order_id": gateway_order_id,
                    "amount": int(order.total_amount * 100),
                    "currency": "INR",
                },
            },
            status=status.HTTP_201_CREATED,
        )
