from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from orders.models import Order, OrderStatusHistory
from payments.models import Payment

from .serializers import VerifyPaymentSerializer
from .services import (
    RazorpayError,
    fetch_razorpay_payment,
    razorpay_is_configured,
    verify_razorpay_signature,
)


class PaymentGatewayError(APIException):
    status_code = 502
    default_detail = "The payment could not be verified with Razorpay."
    default_code = "payment_gateway_error"


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order = Order.objects.filter(pk=data["order_id"], user=request.user).first()
        if order is None:
            raise ValidationError({"order_id": "This order does not exist."})
        payment = order.payments.filter(provider=Payment.Provider.RAZORPAY).first()
        if payment is None:
            raise ValidationError({"order_id": "This order does not have an online payment."})
        if payment.status == Payment.Status.CAPTURED:
            if payment.gateway_payment_id == data["razorpay_payment_id"]:
                return Response({"order": order.pk, "payment_status": order.payment_status})
            raise ValidationError({"payment": "This order has already been paid."})
        if (
            payment.status != Payment.Status.CREATED
            or payment.gateway_order_id != data["razorpay_order_id"]
            or order.payment_status != Order.PaymentStatus.PENDING
        ):
            raise ValidationError({"payment": "This payment is no longer pending."})
        if not razorpay_is_configured():
            raise ValidationError({"payment": "Razorpay test credentials are not configured."})
        if not verify_razorpay_signature(
            data["razorpay_order_id"],
            data["razorpay_payment_id"],
            data["razorpay_signature"],
        ):
            raise ValidationError({"razorpay_signature": "The payment signature is invalid."})
        try:
            gateway_payment = fetch_razorpay_payment(data["razorpay_payment_id"])
        except RazorpayError as error:
            raise PaymentGatewayError() from error

        expected_amount = int(payment.amount * 100)
        if (
            gateway_payment.get("order_id") != payment.gateway_order_id
            or gateway_payment.get("amount") != expected_amount
            or gateway_payment.get("currency") != payment.currency
            or gateway_payment.get("status") != "captured"
        ):
            raise ValidationError(
                {"payment": "Razorpay has not confirmed this payment as captured."}
            )

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk, user=request.user)
            payment = Payment.objects.select_for_update().get(pk=payment.pk, order=order)
            if payment.status == Payment.Status.CAPTURED:
                return Response({"order": order.pk, "payment_status": order.payment_status})
            if payment.status != Payment.Status.CREATED:
                raise ValidationError({"payment": "This payment is no longer pending."})
            payment.status = Payment.Status.CAPTURED
            payment.gateway_payment_id = data["razorpay_payment_id"]
            payment.gateway_signature = data["razorpay_signature"]
            payment.save(
                update_fields=[
                    "status",
                    "gateway_payment_id",
                    "gateway_signature",
                    "updated_at",
                ]
            )
            previous_status = order.status
            order.status = Order.Status.CONFIRMED
            order.payment_status = Order.PaymentStatus.PAID
            order.save(update_fields=["status", "payment_status", "updated_at"])
            cart = Cart.objects.select_for_update().filter(user=request.user).first()
            if cart is not None:
                for item in order.items.all():
                    cart_item = CartItem.objects.select_for_update().filter(
                        cart=cart,
                        product_id=item.product_id,
                    ).first()
                    if cart_item is not None:
                        if cart_item.quantity <= item.quantity:
                            cart_item.delete()
                        else:
                            cart_item.quantity -= item.quantity
                            cart_item.save(update_fields=["quantity", "updated_at"])
            OrderStatusHistory.objects.create(
                order=order,
                previous_status=previous_status,
                status=order.status,
                note="Payment verified with Razorpay.",
                changed_by=request.user,
            )
        return Response(
            {"order": order.pk, "payment_status": order.payment_status},
            status=status.HTTP_200_OK,
        )
