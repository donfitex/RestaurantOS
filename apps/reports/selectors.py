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


def operational_report(branch, start_date, end_date, period="day"):
    from django.db.models import Avg
    from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
    from apps.orders.models import OrderItem
    from apps.inventory.models import StockMovement
    tz = ZoneInfo(branch.restaurant.timezone)
    start = datetime.combine(start_date, time.min, tzinfo=tz)
    end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=tz)
    orders = Order.objects.filter(branch=branch, created_at__gte=start, created_at__lt=end)
    completed = orders.filter(status="COMPLETED")
    trunc = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}[period]
    periods = completed.annotate(period=trunc("created_at", tzinfo=tz)).values("period").annotate(sales=Sum("total"), orders=Count("id")).order_by("period")
    items = OrderItem.objects.filter(order__in=completed)
    stock = InventoryItem.objects.filter(branch=branch)
    movements = StockMovement.objects.filter(inventory_item__branch=branch, created_at__gte=start, created_at__lt=end)
    reservations = Reservation.objects.filter(branch=branch, reservation_date__gte=start_date, reservation_date__lte=end_date)
    return {"branch": branch.pk, "currency": branch.restaurant.currency, "start_date": str(start_date), "end_date": str(end_date), "sales": {"periods": list(periods), "completed_order_value": completed.aggregate(value=Sum("total"), average_order_value=Avg("total")), "by_item": list(items.values("menu_item_id", "name").annotate(quantity=Sum("quantity"), sales=Sum("subtotal")).order_by("-quantity")[:100]), "by_category": list(items.values("menu_item__category_id", "menu_item__category__name").annotate(sales=Sum("subtotal")).order_by("-sales")[:100])}, "orders": list(orders.values("status").annotate(count=Count("id"))), "inventory": {"stock_records": stock.count(), "low_stock": stock.filter(quantity__lte=F("ingredient__minimum_stock")).count(), "movements": list(movements.values("kind", "inventory_item__ingredient__unit").annotate(quantity=Sum("quantity"), count=Count("id")).order_by("kind"))}, "reservations": {"statuses": list(reservations.values("status").annotate(count=Count("id"))), "peak_times": list(reservations.values("start_time").annotate(count=Count("id")).order_by("-count")[:24])}}
