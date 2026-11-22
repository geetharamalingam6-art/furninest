from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from communications.mailer import send_branded_email
from .models import Order, OrderEmailEvent


EVENT_COPY = {
    OrderEmailEvent.Event.CONFIRMATION: ("Your order is confirmed", "Order confirmation", "We have received your order and will keep you updated."),
    OrderEmailEvent.Event.PAYMENT: ("Payment received", "Payment confirmation", "Your payment has been confirmed by our payment provider."),
    OrderEmailEvent.Event.SHIPPED: ("Your order is on its way", "Order shipped", "Your order has been marked as shipped."),
    OrderEmailEvent.Event.DELIVERED: ("Your order has arrived", "Order delivered", "Your order has been marked as delivered."),
    OrderEmailEvent.Event.CANCELLED: ("Your order was cancelled", "Order cancellation", "Your order has been marked as cancelled. Contact support if you need help."),
    OrderEmailEvent.Event.REFUND: ("Your refund is confirmed", "Refund confirmation", "A refund has been confirmed for your order."),
}


def send_order_event(order_id, event):
    now = timezone.now()
    with transaction.atomic():
        order = Order.objects.select_related("user").prefetch_related("items").get(pk=order_id)
        delivery, _ = OrderEmailEvent.objects.get_or_create(order=order, event=event)
        delivery = OrderEmailEvent.objects.select_for_update().get(pk=delivery.pk)
        if delivery.sent_at or (delivery.claimed_at and now - delivery.claimed_at < timedelta(minutes=10)):
            return
        delivery.claimed_at = now
        delivery.save(update_fields=["claimed_at"])

    heading, subject, message = EVENT_COPY[event]
    full_address = ", ".join(
        part for part in (
            order.shipping_address_line_1,
            order.shipping_address_line_2,
            order.shipping_city,
            order.shipping_state,
            order.shipping_postal_code,
            order.shipping_country,
        ) if part
    )
    details = [
        ("Order ID", order.order_number),
        ("Order date", timezone.localtime(order.created_at).strftime("%d %b %Y")),
    ]
    details.extend((f"{item.product_name} x {item.quantity}", f"INR {item.line_total:.2f}") for item in order.items.all())
    details.extend([
        ("Order total", f"INR {order.total_amount:.2f}"),
        ("Payment status", order.get_payment_status_display()),
        ("Delivery to", f"{order.shipping_full_name}, {full_address}"),
    ])
    if order.tracking_number:
        details.append(("Tracking number", order.tracking_number))

    try:
        send_branded_email(
            subject=f"{subject} - {order.order_number}",
            recipient=order.user.email,
            heading=heading,
            greeting=f"Hello {order.user.get_full_name().strip() or 'there'},",
            message=message,
            button_label="View My Orders",
            button_url=f"{settings.FRONTEND_BASE_URL}/orders",
            details=details,
        )
    except Exception:
        with transaction.atomic():
            OrderEmailEvent.objects.filter(pk=delivery.pk, sent_at__isnull=True).update(claimed_at=None)
        raise
    OrderEmailEvent.objects.filter(pk=delivery.pk).update(sent_at=timezone.now(), claimed_at=None)
