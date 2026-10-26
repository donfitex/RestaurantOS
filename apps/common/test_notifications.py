from unittest.mock import patch
from django.core import mail
from django.db import transaction
from django.test import TestCase
from .models import Notification
from .notifications import queue_email, dispatch_pending


class NotificationTests(TestCase):
    def queue(self):
        return queue_email(event_key="test:1", recipient="guest@example.com", subject="Order ready", body="Your order is ready.")

    def test_deduplicated_outbox_and_delivery(self):
        self.queue()
        self.queue()
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(dispatch_pending(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(dispatch_pending(), 0)

    def test_rollback_does_not_send(self):
        try:
            with transaction.atomic():
                self.queue()
                raise ValueError("rollback")
        except ValueError:
            pass
        self.assertFalse(Notification.objects.exists())

    @patch("apps.common.notifications.send_mail", side_effect=OSError("SMTP unavailable"))
    def test_smtp_failure_retains_retry(self, mock):
        self.queue()
        self.assertEqual(dispatch_pending(), 0)
        notification = Notification.objects.get()
        self.assertEqual(notification.status, "PENDING")
        self.assertEqual(notification.attempts, 1)
        self.assertIsNotNone(notification.next_attempt_at)
