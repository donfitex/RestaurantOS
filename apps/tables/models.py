from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import ActiveModel


class Table(ActiveModel):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        OCCUPIED = "OCCUPIED", "Occupied"
        RESERVED = "RESERVED", "Reserved"
        CLEANING = "CLEANING", "Cleaning"
        OUT_OF_SERVICE = "OUT_OF_SERVICE", "Out of service"

    branch = models.ForeignKey(
        "restaurants.Branch", on_delete=models.PROTECT, related_name="tables"
    )
    table_number = models.CharField(max_length=20)
    capacity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    location = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True
    )
    assigned_waiter = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tables",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "table_number"], name="unique_branch_table"),
            models.CheckConstraint(
                condition=models.Q(capacity__gt=0), name="table_capacity_positive"
            ),
        ]
        indexes = [models.Index(fields=["branch", "status", "capacity"])]

    def __str__(self):
        return f"{self.branch} / {self.table_number}"
