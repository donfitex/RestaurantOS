from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Count, Sum, F
from django.utils import timezone
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.reservations.models import Reservation
from apps.tables.models import Table
from apps.inventory.models import InventoryItem


def daily_dashboard(branch):
    tz = ZoneInfo(branch.restaurant.timezone)
    today = timezone.now().astimezone(tz).date()
    start = datetime.combine(today, time.min, tzinfo=tz)
    end = datetime.combine(today + timedelta(days=1), time.min, tzinfo=tz)
    orders = Order.objects.filter(branch=branch)
    payments = Payment.objects.filter(order__branch=branch, status__in=["PAID", "PARTIALLY_REFUNDED", "REFUNDED"], paid_at__gte=start, paid_at__lt=end)
    tables = dict(Table.objects.filter(branch=branch, is_active=True).values_list("status").annotate(count=Count("id")))
    return {"branch": branch.pk, "date": str(today), "currency": branch.restaurant.currency, "sales": str(payments.aggregate(total=Sum(F("amount") - F("refunded_amount")))["total"] or 0), "orders": orders.filter(created_at__gte=start, created_at__lt=end).count(), "active_orders": orders.exclude(status__in=["COMPLETED", "CANCELLED"]).count(), "reservations": Reservation.objects.filter(branch=branch, reservation_date=today).exclude(status="CANCELLED").count(), "available_tables": tables.get("AVAILABLE", 0), "occupied_tables": tables.get("OCCUPIED", 0), "low_stock": InventoryItem.objects.filter(branch=branch, quantity__lte=F("ingredient__minimum_stock")).count()}
