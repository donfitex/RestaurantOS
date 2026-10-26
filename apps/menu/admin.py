from django.contrib import admin
from apps.common.admin import DomainAdmin
from .models import MenuCategory, MenuItem, MenuModifier, MenuItemModifier


class ModifierInline(admin.TabularInline):
    model = MenuItemModifier
    extra = 0


@admin.register(MenuItem)
class MenuItemAdmin(DomainAdmin):
    list_display = ("name", "branch", "category", "price", "availability", "is_active")
    list_filter = ("branch", "category", "availability", "is_active")
    search_fields = ("name", "sku", "description")
    list_select_related = ("branch", "category")
    inlines = (ModifierInline,)


@admin.register(MenuCategory)
class CategoryAdmin(DomainAdmin):
    list_display = ("name", "restaurant", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name",)


@admin.register(MenuModifier)
class ModifierAdmin(DomainAdmin):
    list_display = ("name", "restaurant", "price", "is_active")
    search_fields = ("name",)
    list_filter = ("restaurant", "is_active")
