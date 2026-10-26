from decimal import Decimal
from typing import Protocol

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import Conflict
from apps.orders.models import Order

from .models import Payment, Refund

SETTLED = ["PAID", "PARTIALLY_REFUNDED", "REFUNDED"]


class PaymentProvider(Protocol):
    def verify(self, reference: str, amount: Decimal, currency: str) -> bool: ...


def validate_amount(value):
    value = Decimal(str(value))
    if not value.is_finite() or value <= 0 or value != value.quantize(Decimal("0.01")):
        raise ValidationError("Use a positive amount with at most two decimal places.")
    return value


def settled_total(order):
    return order.payments.filter(status__in=SETTLED).aggregate(
        total=Sum(F("amount") - F("refunded_amount"))
    )["total"] or Decimal("0")


@transaction.atomic
def record_payment(*, order, amount, method, reference, actor):
    order = Order.objects.select_for_update().get(pk=order.pk)
    amount = validate_amount(amount)
    existing = Payment.objects.filter(reference=reference).first()
    if existing:
        if (
            existing.order_id == order.pk
            and existing.amount == amount
            and existing.method == method
        ):
            return existing
        raise Conflict("Payment reference already belongs to another transaction.")
    if order.status == "CANCELLED" or amount > order.total - settled_total(order):
        raise Conflict("Payment exceeds the outstanding balance or the order is cancelled.")
    if method not in Payment.Method.values:
        raise ValidationError("Unsupported payment method.")
    payment = Payment.objects.create(
        order=order,
        amount=amount,
        currency=order.currency,
        method=method,
        reference=reference,
        recorded_by=actor,
        status="PAID",
        paid_at=timezone.now(),
    )
    from apps.common.notifications import queue_email

    queue_email(
        event_key=f"payment:{payment.pk}:PAID",
        recipient=order.customer.email,
        subject=f"Payment received for order #{order.pk}",
        body=f"Payment of {order.currency} {amount} has been recorded. Reference: {reference}.",
    )
    return payment


@transaction.atomic
def refund_payment(*, payment, amount, reference, reason, actor):
    Order.objects.select_for_update().get(pk=payment.order_id)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    amount = validate_amount(amount)
    existing = Refund.objects.filter(reference=reference).first()
    if existing:
        if existing.payment_id == payment.pk and existing.amount == amount:
            return existing
        raise Conflict("Refund reference was already used.")
    if payment.status not in SETTLED or amount > payment.amount - payment.refunded_amount:
        raise Conflict("Refund exceeds the refundable balance.")
    refund = Refund.objects.create(
        payment=payment, amount=amount, reference=reference, reason=reason, actor=actor
    )
    payment.refunded_amount += amount
    payment.status = (
        "REFUNDED" if payment.refunded_amount == payment.amount else "PARTIALLY_REFUNDED"
    )
    payment.save(update_fields=["refunded_amount", "status", "updated_at"])
    return refund
