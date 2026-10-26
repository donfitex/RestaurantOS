import logging
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.utils import timezone

from .models import WorkerHeartbeat

logger = logging.getLogger(__name__)


def liveness(request):
    return JsonResponse({"status": "alive"})


def readiness(request):
    checks = {"database": "ok"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        if getattr(settings, "REQUIRE_NOTIFICATION_WORKER", False):
            threshold = timezone.now() - timedelta(seconds=90)
            checks["notification_worker"] = (
                "ok"
                if WorkerHeartbeat.objects.filter(
                    name="notifications", last_seen_at__gte=threshold
                ).exists()
                else "unavailable"
            )
    except DatabaseError as exc:
        checks["database"] = "unavailable"
        logger.error("readiness_database_failed", extra={"error_type": type(exc).__name__})
    healthy = all(value == "ok" for value in checks.values())
    response = JsonResponse(
        {"status": "healthy" if healthy else "unhealthy", **checks}, status=200 if healthy else 503
    )
    response["Cache-Control"] = "no-store"
    return response
