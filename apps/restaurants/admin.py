from django.contrib import admin
from apps.common.admin import DomainAdmin
from .models import Restaurant, Branch, OperatingHours


class HoursInline(admin.TabularInline):
    model = OperatingHours
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(DomainAdmin):
    list_display = ("name", "currency", "timezone", "is_active")
    search_fields = ("name", "address")
    list_filter = ("is_active", "currency")


@admin.register(Branch)
class BranchAdmin(DomainAdmin):
    list_display = ("name", "restaurant", "tax_rate", "is_active")
    search_fields = ("name", "address")
    list_filter = ("restaurant", "is_active")
    filter_horizontal = ("staff", "managers")
    inlines = (HoursInline,)
