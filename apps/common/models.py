from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ActiveModel(TimestampedModel):
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta(TimestampedModel.Meta):
        abstract = True


class Notification(TimestampedModel):
    event_key = models.CharField(max_length=200)
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=10, default="PENDING", db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_key", "recipient"], name="unique_notification_recipient"
            )
        ]


class RateLimitBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)


class WorkerHeartbeat(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    last_seen_at = models.DateTimeField()


class AuditEvent(TimestampedModel):
    actor = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(
        "restaurants.Branch", on_delete=models.PROTECT, null=True, blank=True
    )
    event = models.CharField(max_length=80, db_index=True)
    object_type = models.CharField(max_length=40)
    object_id = models.CharField(max_length=40)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [models.Index(fields=["branch", "created_at"])]
