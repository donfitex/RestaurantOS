from django.contrib import admin
from apps.common.admin import DomainAdmin
from .models import Table


@admin.register(Table)
class TableAdmin(DomainAdmin):
    list_display = ("table_number", "branch", "capacity", "status", "is_active")
    list_filter = ("branch", "status", "is_active")
    search_fields = ("table_number", "location")
    list_select_related = ("branch",)
