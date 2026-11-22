from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from coupons.models import Coupon
from orders.models import InventoryTransaction, Order, OrderStatusHistory
from orders.serializers import OrderSerializer
from payments.models import Payment
from products.models import Product


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices, required=False)
    tracking_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    note = serializers.CharField(max_length=255, required=False, allow_blank=True)


class DashboardOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        order_stats = Order.objects.aggregate(
            total_orders=Count("id"),
            paid_revenue=Sum(
                "total_amount",
                filter=Q(payment_status=Order.PaymentStatus.PAID),
            ),
            to_fulfill=Count(
                "id",
                filter=Q(
                    status__in=[
                        Order.Status.PENDING,
                        Order.Status.CONFIRMED,
                        Order.Status.PROCESSING,
                        Order.Status.SHIPPED,
                        Order.Status.OUT_FOR_DELIVERY,
                    ]
                ),
            ),
        )
        low_stock = Product.objects.filter(is_active=True, stock_quantity__lte=5)
        status_counts = {
            entry["status"]: entry["count"]
            for entry in Order.objects.values("status").annotate(count=Count("id"))
        }
        recent_orders = Order.objects.prefetch_related("items", "status_history")[:5]
        low_stock_products = low_stock.values(
            "id",
            "name",
            "sku",
            "stock_quantity",
        )[:10]
        return Response(
            {
                "total_orders": order_stats["total_orders"],
                "paid_revenue": order_stats["paid_revenue"] or 0,
                "to_fulfill": order_stats["to_fulfill"],
                "active_products": Product.objects.filter(is_active=True).count(),
                "active_coupons": Coupon.objects.filter(is_active=True).count(),
                "low_stock_count": low_stock.count(),
                "orders_by_status": status_counts,
                "recent_orders": OrderSerializer(recent_orders, many=True).data,
                "low_stock_products": list(low_stock_products),
            }
        )


class DashboardOrderListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Order.objects.prefetch_related("items", "status_history")
        status_filter = request.query_params.get("status", "")
        if status_filter:
            if status_filter not in Order.Status.values:
                raise ValidationError({"status": "Choose a valid order status."})
            orders = orders.filter(status=status_filter)
        search = request.query_params.get("search", "").strip()
        if search:
            orders = orders.filter(
                Q(order_number__icontains=search)
                | Q(user__email__icontains=search)
                | Q(shipping_full_name__icontains=search)
            )
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(orders, request, view=self)
        return paginator.get_paginated_response(OrderSerializer(page, many=True).data)


class DashboardOrderStatusView(APIView):
    permission_classes = [IsAdminUser]

    allowed_transitions = {
        Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
        Order.Status.CONFIRMED: {Order.Status.PROCESSING, Order.Status.CANCELLED},
        Order.Status.PROCESSING: {Order.Status.SHIPPED, Order.Status.CANCELLED},
        Order.Status.SHIPPED: {Order.Status.OUT_FOR_DELIVERY},
        Order.Status.OUT_FOR_DELIVERY: {Order.Status.DELIVERED},
        Order.Status.DELIVERED: set(),
        Order.Status.CANCELLED: set(),
        Order.Status.RETURNED: set(),
    }

    def patch(self, request, order_id):
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(pk=order_id).first()
            if order is None:
                raise NotFound("This order does not exist.")
            previous_status = order.status
            next_status = data.get("status", previous_status)
            if next_status != previous_status:
                if next_status not in self.allowed_transitions[previous_status]:
                    raise ValidationError(
                        {"status": f"An order cannot move from {previous_status} to {next_status}."}
                    )
                if next_status == Order.Status.CANCELLED:
                    if (
                        order.payment_method != Order.PaymentMethod.COD
                        or order.payment_status != Order.PaymentStatus.UNPAID
                    ):
                        raise ValidationError(
                            {"status": "Only unpaid cash-on-delivery orders can be cancelled here."}
                        )
                    self.release_stock(order, request)
                    if order.coupon_id is not None:
                        Coupon.objects.filter(pk=order.coupon_id, used_count__gt=0).update(
                            used_count=F("used_count") - 1
                        )
                    order.cancelled_at = timezone.now()
                if (
                    next_status == Order.Status.DELIVERED
                    and order.payment_method == Order.PaymentMethod.COD
                ):
                    order.payment_status = Order.PaymentStatus.PAID
                    Payment.objects.filter(
                        order=order,
                        provider=Payment.Provider.COD,
                        status=Payment.Status.CREATED,
                    ).update(status=Payment.Status.CAPTURED, updated_at=timezone.now())
                order.status = next_status
                order.save(
                    update_fields=[
                        "status",
                        "payment_status",
                        "cancelled_at",
                        "updated_at",
                    ]
                )
                OrderStatusHistory.objects.create(
                    order=order,
                    previous_status=previous_status,
                    status=next_status,
                    note=data.get("note", ""),
                    changed_by=request.user,
                )
            if "tracking_number" in data and data["tracking_number"] != order.tracking_number:
                order.tracking_number = data["tracking_number"]
                order.save(update_fields=["tracking_number", "updated_at"])
        order = Order.objects.prefetch_related("items", "status_history").get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

    @staticmethod
    def release_stock(order, request):
        for item in order.items.select_for_update():
            product = Product.objects.select_for_update().get(pk=item.product_id)
            product.stock_quantity += item.quantity
            product.save(update_fields=["stock_quantity", "updated_at"])
            InventoryTransaction.objects.create(
                product=product,
                order_item=item,
                reason=InventoryTransaction.Reason.CANCELLATION,
                quantity_change=item.quantity,
                stock_after=product.stock_quantity,
                note=f"Released after cancellation of {order.order_number}.",
                changed_by=request.user,
            )
