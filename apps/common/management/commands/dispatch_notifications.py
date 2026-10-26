from django.core.management.base import BaseCommand
from apps.common.notifications import dispatch_pending


class Command(BaseCommand):
    help = "Send up to 100 queued email notifications, retrying transient failures."

    def handle(self, *args, **options):
        self.stdout.write(f"Sent {dispatch_pending()} notifications")
