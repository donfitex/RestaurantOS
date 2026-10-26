from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from apps.common.admin import AdministratorAccess


@admin.register(User)
class RestaurantUserAdmin(AdministratorAccess, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Restaurant profile", {"fields": ("role", "phone", "preferences")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Restaurant profile", {"fields": ("email", "role")}),)
    list_display = ("username", "email", "role", "is_active")
    list_filter = UserAdmin.list_filter + ("role",)
