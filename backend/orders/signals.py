import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .emailing import send_order_event
from .models import Order, OrderEmailEvent

logger = logging.getLogger(__name__)


def send_order_event_safely(order_id, event):
    try:
        send_order_event(order_id, event)
    except Exception:
        logger.exception("Could not send order notification (order_id=%s, event=%s).", order_id, event)


@receiver(pre_save, sender=Order)
def remember_previous_email_status(sender, instance, **kwargs):
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).values("status", "payment_status").first()
        instance._previous_email_status = old or {}
    else:
        instance._previous_email_status = {}


@receiver(post_save, sender=Order)
def notify_order_changes(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_email_status", {})
    events = []
    if instance.status == Order.Status.CONFIRMED and (
        created or previous.get("status") != Order.Status.CONFIRMED
    ):
        events.append(OrderEmailEvent.Event.CONFIRMATION)
    if instance.payment_status == Order.PaymentStatus.PAID and (
        created or previous.get("payment_status") != Order.PaymentStatus.PAID
    ):
        events.append(OrderEmailEvent.Event.PAYMENT)
    if not created and previous.get("status") != instance.status:
        event_by_status = {
            Order.Status.SHIPPED: OrderEmailEvent.Event.SHIPPED,
            Order.Status.DELIVERED: OrderEmailEvent.Event.DELIVERED,
            Order.Status.CANCELLED: OrderEmailEvent.Event.CANCELLED,
        }
        if instance.status in event_by_status:
            events.append(event_by_status[instance.status])
    if instance.payment_status == Order.PaymentStatus.REFUNDED and (
        created or previous.get("payment_status") != Order.PaymentStatus.REFUNDED
    ):
        events.append(OrderEmailEvent.Event.REFUND)

    for event in events:
        transaction.on_commit(
            lambda order_id=instance.pk, order_event=event: send_order_event_safely(
                order_id, order_event
            )
        )
