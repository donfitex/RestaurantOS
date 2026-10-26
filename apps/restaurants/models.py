from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import ActiveModel, TimestampedModel


def validate_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValidationError("Use a valid IANA timezone.") from None


class Restaurant(ActiveModel):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    timezone = models.CharField(
        max_length=64, default="Africa/Lagos", validators=[validate_timezone]
    )
    currency = models.CharField(max_length=3, default="NGN")

    def __str__(self):
        return self.name


class Branch(ActiveModel):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=160)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="managed_branches"
    )
    staff = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="branches")
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["restaurant", "name"], name="unique_restaurant_branch"),
            models.CheckConstraint(
                condition=models.Q(tax_rate__gte=0, tax_rate__lte=1), name="branch_tax_range"
            ),
        ]

    def __str__(self):
        return f"{self.restaurant}: {self.name}"


class OperatingHours(TimestampedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="operating_hours")
    weekday = models.PositiveSmallIntegerField(validators=[MaxValueValidator(6)])
    opens_at = models.TimeField()
    closes_at = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "weekday"], name="unique_branch_weekday"),
            models.CheckConstraint(
                condition=models.Q(closes_at__gt=models.F("opens_at")), name="hours_end_after_start"
            ),
            models.CheckConstraint(condition=models.Q(weekday__lte=6), name="valid_weekday"),
        ]
