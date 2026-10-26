from django.db.models.signals import post_save
from django.dispatch import receiver

from .alerts import sync_stock_alert
from .models import Ingredient, InventoryItem


@receiver(post_save, sender=InventoryItem)
def stock_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        sync_stock_alert(instance)


@receiver(post_save, sender=Ingredient)
def threshold_changed(sender, instance, raw=False, **kwargs):
    if not raw:
        for stock in instance.stock.select_related("ingredient").iterator():
            sync_stock_alert(stock)
