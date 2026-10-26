from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimestampedModel


class Reservation(TimestampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        SEATED = "SEATED", "Seated"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        NO_SHOW = "NO_SHOW", "No show"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservations")
    branch = models.ForeignKey("restaurants.Branch", on_delete=models.PROTECT, related_name="reservations")
    table = models.ForeignKey("tables.Table", on_delete=models.PROTECT, related_name="reservations")
    guest_count = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    reservation_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    special_requests = models.TextField(blank=True)
    guest_name = models.CharField(max_length=160, blank=True)
    guest_phone = models.CharField(max_length=32, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(end_time__gt=models.F("start_time")), name="reservation_end_after_start"), models.CheckConstraint(condition=models.Q(guest_count__gt=0), name="reservation_guests_positive")]
        indexes = [models.Index(fields=["table", "reservation_date", "status"]), models.Index(fields=["branch", "reservation_date"])]

    def clean(self):
        if self.table_id and self.branch_id and self.table.branch_id != self.branch_id:
            raise ValidationError({"table": "Table must belong to the selected branch."})
        if self.table_id and self.guest_count and self.guest_count > self.table.capacity:
            raise ValidationError({"guest_count": "Guest count exceeds table capacity."})
