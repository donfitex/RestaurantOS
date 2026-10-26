from decimal import Decimal
from django.utils import timezone
from .models import StockAlert


def sync_stock_alert(stock):
    low = Decimal(str(stock.quantity)) <= Decimal(str(stock.ingredient.minimum_stock))
    alert = StockAlert.objects.filter(inventory_item=stock).first()
    if low and alert is None:
        alert = StockAlert.objects.create(inventory_item=stock)
        from apps.common.notifications import notify_low_stock
        notify_low_stock(stock, alert)
        return alert
    if alert is not None and alert.is_active != low:
        alert.is_active = low
        alert.resolved_at = None if low else timezone.now()
        alert.save(update_fields=["is_active", "resolved_at", "updated_at"])
        if low:
            from apps.common.notifications import notify_low_stock
            notify_low_stock(stock, alert)
    return alert
