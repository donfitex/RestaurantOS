from django.contrib import admin

from apps.users.permissions import is_admin

from .models import Notification


class AdministratorAccess:
    def has_module_permission(self, request):
        return is_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return is_admin(request.user)

    def has_add_permission(self, request):
        return is_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return False


class DomainAdmin(AdministratorAccess, admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50


class LedgerAdmin(DomainAdmin):
    """Operational and financial state changes must go through services."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


@admin.register(Notification)
class NotificationAdmin(LedgerAdmin):
    list_display = ("id", "subject", "status", "attempts", "sent_at")
    list_filter = ("status", "created_at")
    search_fields = ("event_key", "subject")
