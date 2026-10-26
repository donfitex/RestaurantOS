from django.contrib import admin
from apps.common.admin import LedgerAdmin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(LedgerAdmin):
    list_display = ("id", "order", "amount", "currency", "method", "status", "reference")
    list_filter = ("method", "status", "order__branch")
    search_fields = ("reference", "order__customer__username")
    list_select_related = ("order",)


@admin.register(Refund)
class RefundAdmin(LedgerAdmin):
    list_display = ("id", "payment", "amount", "reference", "actor", "created_at")
    search_fields = ("reference", "reason")
    list_filter = ("created_at",)
