import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        event = (
            "django_request_error"
            if record.name.startswith(("django.request", "django.security"))
            else record.getMessage()
        )
        result = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": event,
        }
        for name in [
            "request_id",
            "method",
            "route",
            "status_code",
            "duration_ms",
            "user_id",
            "event_name",
            "object_type",
            "object_id",
            "notification_id",
            "sent_count",
            "error_type",
        ]:
            if hasattr(record, name):
                result[name] = getattr(record, name)
        if record.exc_info:
            result["error_type"] = record.exc_info[0].__name__
        return json.dumps(result, default=str)
