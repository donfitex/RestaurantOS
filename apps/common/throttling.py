import hashlib
import hmac
import time
from datetime import datetime, timezone
from django.conf import settings
from django.db.models import F
from rest_framework.throttling import BaseThrottle
from .models import RateLimitBucket


def consume(scope, identity, limit, seconds=60):
    now = time.time()
    window = int(now // seconds)
    key = hmac.new(settings.SECRET_KEY.encode(), f"{scope}:{identity}:{window}".encode(), hashlib.sha256).hexdigest()
    bucket, _ = RateLimitBucket.objects.get_or_create(key=key, defaults={"expires_at": datetime.fromtimestamp((window + 1) * seconds, tz=timezone.utc)})
    return bool(RateLimitBucket.objects.filter(pk=bucket.pk, count__lt=limit).update(count=F("count") + 1))


class DatabaseRateThrottle(BaseThrottle):
    """Atomic counters shared by all workers; do not trust forwarded client headers."""
    def allow_request(self, request, view):
        authenticated = request.user.is_authenticated
        identity = str(request.user.pk) if authenticated else request.META.get("REMOTE_ADDR", "unknown")
        return consume("user" if authenticated else "anonymous", identity, 600 if authenticated else 60)

    def wait(self):
        return 60 - time.time() % 60
