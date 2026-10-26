from django.contrib import admin

from apps.common.admin import LedgerAdmin

from .models import Order, OrderItem


class ItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("name", "quantity", "unit_price", "subtotal", "notes")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(LedgerAdmin):
    list_display = (
        "id",
        "branch",
        "customer",
        "order_type",
        "status",
        "total",
        "currency",
        "created_at",
    )
    list_filter = ("branch", "status", "order_type", "created_at")
    search_fields = ("customer__username", "notes", "request_key")
    list_select_related = ("branch", "customer")
    inlines = (ItemInline,)
