import logging

from .models import AuditEvent

logger = logging.getLogger(__name__)


def record_event(event, obj, *, actor=None, branch=None, metadata=None):
    audit = AuditEvent.objects.create(
        event=event,
        object_type=obj._meta.label_lower,
        object_id=str(obj.pk),
        actor=actor,
        branch=branch,
        metadata=metadata or {},
    )
    logger.info(
        "domain_event",
        extra={
            "event_name": event,
            "object_type": obj._meta.label_lower,
            "object_id": str(obj.pk),
            "user_id": actor.pk if actor else None,
        },
    )
    return audit
