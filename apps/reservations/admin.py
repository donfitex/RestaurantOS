from django.contrib import admin

from apps.common.admin import LedgerAdmin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(LedgerAdmin):
    list_display = (
        "id",
        "customer",
        "branch",
        "table",
        "reservation_date",
        "start_time",
        "guest_count",
        "status",
    )
    list_filter = ("branch", "status", "reservation_date")
    search_fields = ("guest_name", "guest_phone", "customer__username")
    list_select_related = ("branch", "table", "customer")
