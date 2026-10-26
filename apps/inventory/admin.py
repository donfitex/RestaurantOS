from django.contrib import admin
from apps.common.admin import DomainAdmin, LedgerAdmin
from .models import Ingredient, InventoryItem, StockMovement, Supplier, Recipe, RecipeIngredient, StockAlert


@admin.register(Ingredient)
class IngredientAdmin(DomainAdmin):
    list_display = ("name", "restaurant", "sku", "unit", "minimum_stock", "is_active")
    list_filter = ("restaurant", "unit", "is_active")
    search_fields = ("name", "sku")


@admin.register(InventoryItem)
class InventoryAdmin(DomainAdmin):
    list_display = ("ingredient", "branch", "quantity", "updated_at")
    list_filter = ("branch",)
    search_fields = ("ingredient__name", "ingredient__sku")
    readonly_fields = DomainAdmin.readonly_fields + ("quantity",)
    list_select_related = ("ingredient", "branch")


@admin.register(StockMovement)
class MovementAdmin(LedgerAdmin):
    list_display = ("id", "inventory_item", "kind", "quantity", "balance_after", "actor", "created_at")
    list_filter = ("kind", "inventory_item__branch", "created_at")
    search_fields = ("reference", "notes", "inventory_item__ingredient__name")
    list_select_related = ("inventory_item__ingredient", "actor")


@admin.register(Supplier)
class SupplierAdmin(DomainAdmin):
    list_display = ("name", "restaurant", "email", "phone", "is_active")
    list_filter = ("restaurant", "is_active")
    search_fields = ("name", "email")


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(DomainAdmin):
    list_display = ("menu_item", "updated_at")
    search_fields = ("menu_item__name",)
    list_filter = ("menu_item__branch",)
    inlines = (RecipeIngredientInline,)


@admin.register(StockAlert)
class AlertAdmin(LedgerAdmin):
    list_display = ("inventory_item", "kind", "is_active", "resolved_at")
    list_filter = ("is_active", "inventory_item__branch")
    search_fields = ("inventory_item__ingredient__name",)
