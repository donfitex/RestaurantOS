import logging
import signal
from threading import Event

from django.core.management.base import BaseCommand

from apps.common.notifications import dispatch_pending

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the notification outbox worker with graceful shutdown."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=10)
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        if options["interval"] < 1:
            raise ValueError("Interval must be positive")
        stopped = Event()
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: stopped.set())
        while not stopped.is_set():
            try:
                count = dispatch_pending()
                from django.utils import timezone

                from apps.common.models import RateLimitBucket, WorkerHeartbeat

                WorkerHeartbeat.objects.update_or_create(
                    name="notifications", defaults={"last_seen_at": timezone.now()}
                )
                RateLimitBucket.objects.filter(expires_at__lt=timezone.now()).delete()
                logger.info("notification_batch_completed", extra={"sent_count": count})
            except Exception:
                logger.exception("notification_worker_error")
            if options["once"]:
                break
            stopped.wait(options["interval"])
