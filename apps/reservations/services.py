from datetime import datetime
from zoneinfo import ZoneInfo
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.common.exceptions import Conflict
from apps.restaurants.models import OperatingHours
from apps.tables.models import Table
from .models import Reservation

ACTIVE_STATUSES = [Reservation.Status.PENDING, Reservation.Status.CONFIRMED, Reservation.Status.SEATED]


def validate_slot(branch, reservation_date, start_time, end_time, guest_count):
    if guest_count < 1 or start_time >= end_time:
        raise ValidationError("Choose a positive guest count and an end time after the start.")
    local_start = datetime.combine(reservation_date, start_time, tzinfo=ZoneInfo(branch.restaurant.timezone))
    if local_start <= timezone.now():
        raise ValidationError("Reservations must start in the future.")
    hours = OperatingHours.objects.filter(branch=branch, weekday=reservation_date.weekday()).first()
    if hours is None or start_time < hours.opens_at or end_time > hours.closes_at:
        raise ValidationError("The selected time is outside branch operating hours.")


def available_tables(*, branch, reservation_date, start_time, end_time, guest_count):
    validate_slot(branch, reservation_date, start_time, end_time, guest_count)
    conflicts = Reservation.objects.filter(branch=branch, reservation_date=reservation_date, status__in=ACTIVE_STATUSES, start_time__lt=end_time, end_time__gt=start_time).values("table_id")
    return Table.objects.filter(branch=branch, branch__is_active=True, branch__restaurant__is_active=True, is_active=True, capacity__gte=guest_count).exclude(status__in=[Table.Status.OUT_OF_SERVICE, Table.Status.CLEANING]).exclude(pk__in=conflicts).order_by("capacity", "table_number")


@transaction.atomic
def create_reservation(*, customer, table, reservation_date, start_time, end_time, guest_count, special_requests="", guest_name="", guest_phone=""):
    table = Table.objects.select_for_update().select_related("branch__restaurant").get(pk=table.pk)
    if not available_tables(branch=table.branch, reservation_date=reservation_date, start_time=start_time, end_time=end_time, guest_count=guest_count).filter(pk=table.pk).exists():
        raise Conflict("The table is unavailable for this time and party size.")
    return Reservation.objects.create(customer=customer, branch=table.branch, table=table, reservation_date=reservation_date, start_time=start_time, end_time=end_time, guest_count=guest_count, special_requests=special_requests, guest_name=guest_name, guest_phone=guest_phone)


@transaction.atomic
def transition_reservation(reservation, target):
    Table.objects.select_for_update().get(pk=reservation.table_id)
    reservation = Reservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.status == target:
        return reservation
    allowed = {"PENDING": {"CONFIRMED", "CANCELLED"}, "CONFIRMED": {"SEATED", "CANCELLED", "NO_SHOW"}, "SEATED": {"COMPLETED"}}
    if target not in allowed.get(reservation.status, set()):
        raise Conflict("Invalid reservation status transition.")
    if target == "SEATED":
        table = Table.objects.get(pk=reservation.table_id)
        if table.status != Table.Status.AVAILABLE:
            raise Conflict("Table is not available for seating.")
        table.status = Table.Status.OCCUPIED
        table.save(update_fields=["status", "updated_at"])
    elif target == "COMPLETED":
        Table.objects.filter(pk=reservation.table_id).update(status=Table.Status.CLEANING)
    reservation.status = target
    reservation.save(update_fields=["status", "updated_at"])
    return reservation
