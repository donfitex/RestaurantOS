from datetime import timedelta
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Notification

logger = logging.getLogger(__name__)


def queue_email(*, event_key, recipient, subject, body):
    if recipient:
        notification, _ = Notification.objects.get_or_create(event_key=event_key, recipient=recipient, defaults={"subject": subject, "body": body})
        return notification


def notify_order(order, event):
    queue_email(event_key=f"order:{order.pk}:{event}", recipient=order.customer.email, subject=f"Order #{order.pk}: {event.replace('_', ' ').title()}", body=f"Your order #{order.pk} at {order.branch.name} is {event.lower()}. Total: {order.currency} {order.total}.")


def notify_reservation(reservation, event):
    queue_email(event_key=f"reservation:{reservation.pk}:{event}", recipient=reservation.customer.email, subject=f"Reservation #{reservation.pk}: {event.title()}", body=f"Your table reservation at {reservation.branch.name} on {reservation.reservation_date}, {reservation.start_time} to {reservation.end_time}, is {event.lower()}.")


def notify_low_stock(stock, alert):
    from django.contrib.auth import get_user_model
    recipients = get_user_model().objects.filter(Q(managed_branches=stock.branch) | Q(branches=stock.branch, role__in=["MANAGER", "INVENTORY_MANAGER"]), is_active=True).distinct()
    for user in recipients:
        queue_email(event_key=f"stock:{alert.pk}:{alert.updated_at.isoformat()}", recipient=user.email, subject=f"Low stock: {stock.ingredient.name}", body=f"{stock.branch.name}: {stock.quantity} {stock.ingredient.unit} remaining. Minimum: {stock.ingredient.minimum_stock}.")


def dispatch_pending(limit=100):
    sent = 0
    for _ in range(limit):
        with transaction.atomic():
            qs = Notification.objects.filter(status="PENDING").filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=timezone.now())).order_by("created_at")
            from django.db import connection
            qs = qs.select_for_update(skip_locked=True) if connection.features.has_select_for_update_skip_locked else qs.select_for_update()
            notification = qs.first()
            if notification is None:
                break
            notification.attempts += 1
            try:
                result = send_mail(notification.subject, notification.body, settings.DEFAULT_FROM_EMAIL, [notification.recipient], fail_silently=False)
                if result != 1:
                    raise RuntimeError("Email backend did not accept the message")
            except Exception as exc:
                notification.last_error = type(exc).__name__
                notification.next_attempt_at = timezone.now() + timedelta(minutes=min(60, 2 ** notification.attempts))
                if notification.attempts >= 5:
                    notification.status = "FAILED"
                logger.warning("notification_delivery_failed", extra={"notification_id": notification.pk, "error_type": type(exc).__name__})
            else:
                notification.status = "SENT"
                notification.sent_at = timezone.now()
                notification.last_error = ""
                sent += 1
            notification.save()
    return sent
