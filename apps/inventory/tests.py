from decimal import Decimal
from django.db import IntegrityError, transaction
from django.test import TestCase
from apps.restaurants.models import Restaurant, Branch
from .models import Ingredient, InventoryItem


class InventoryModelTests(TestCase):
    def test_database_prevents_negative_inventory(self):
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Central")
        ingredient = Ingredient.objects.create(restaurant=restaurant, name="Rice", sku="rice", unit="KG")
        with self.assertRaises(IntegrityError), transaction.atomic():
            InventoryItem.objects.create(branch=branch, ingredient=ingredient, quantity=Decimal("-1"))


class RecipeTests(TestCase):
    def test_cross_restaurant_recipe_rejected(self):
        from apps.menu.models import MenuCategory, MenuItem
        from .recipes import replace_recipe
        from .models import Recipe
        from rest_framework.exceptions import ValidationError
        restaurant = Restaurant.objects.create(name="One")
        other = Restaurant.objects.create(name="Two")
        branch = Branch.objects.create(restaurant=restaurant, name="Main")
        category = MenuCategory.objects.create(restaurant=restaurant, name="Mains")
        item = MenuItem.objects.create(branch=branch, category=category, name="Rice", sku="rice", price="1000")
        ingredient = Ingredient.objects.create(restaurant=other, name="Rice", sku="rice", unit="KG")
        with self.assertRaises(ValidationError):
            replace_recipe(menu_item=item, ingredients=[{"ingredient": ingredient.pk, "quantity": "0.250"}])
        self.assertFalse(Recipe.objects.exists())


class StockDeductionTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from apps.menu.models import MenuCategory, MenuItem
        from apps.orders.services import create_order
        from .models import Recipe, RecipeIngredient
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Main")
        category = MenuCategory.objects.create(restaurant=restaurant, name="Mains")
        item = MenuItem.objects.create(branch=branch, category=category, name="Rice", sku="rice", price="1000")
        ingredient = Ingredient.objects.create(restaurant=restaurant, name="Rice", sku="rice", unit="KG")
        self.stock = InventoryItem.objects.create(branch=branch, ingredient=ingredient, quantity="5")
        recipe = Recipe.objects.create(menu_item=item)
        self.recipe_line = RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity="2")
        user = get_user_model().objects.create_user(username="guest", email="guest@example.com")
        self.order = create_order(customer=user, branch=branch, items=[{"menu_item": item.pk, "quantity": 2}])

    def test_confirmation_and_cancellation_are_idempotent(self):
        from apps.orders.services import transition_order
        from .models import StockMovement
        transition_order(self.order, "CONFIRMED")
        transition_order(self.order, "CONFIRMED")
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("1"))
        self.recipe_line.quantity = "1"
        self.recipe_line.save()
        transition_order(self.order, "CANCELLED")
        transition_order(self.order, "CANCELLED")
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("5"))
        self.assertEqual(StockMovement.objects.count(), 2)

    def test_insufficient_stock_rolls_back_status_and_movements(self):
        from apps.orders.services import transition_order
        from apps.common.exceptions import Conflict
        from .models import StockMovement
        self.stock.quantity = "3"
        self.stock.save()
        with self.assertRaises(Conflict):
            transition_order(self.order, "CONFIRMED")
        self.order.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(self.order.status, "PENDING")
        self.assertEqual(self.stock.quantity, Decimal("3"))
        self.assertFalse(StockMovement.objects.exists())

    def test_stock_api_requires_branch_membership(self):
        from django.contrib.auth import get_user_model
        from rest_framework.test import APIClient
        user = get_user_model().objects.create_user(username="stock", email="stock@example.com", role="INVENTORY_MANAGER")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get("/api/v1/inventory/").data["count"], 0)
        self.stock.branch.staff.add(user)
        response = client.post("/api/v1/inventory/restock/", {"inventory_item": self.stock.pk, "quantity": "2", "notes": "Delivery"})
        self.assertEqual(response.status_code, 201, response.data)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, Decimal("7"))
        self.assertEqual(client.get(f"/api/v1/inventory/{self.stock.pk}/movements/").data["count"], 1)

    def test_alert_resolves_after_restock(self):
        from .models import StockAlert
        from .services import adjust_stock
        self.stock.ingredient.minimum_stock = Decimal("5")
        self.stock.ingredient.save()
        self.assertTrue(StockAlert.objects.get(inventory_item=self.stock).is_active)
        adjust_stock(inventory_item=self.stock, quantity="1", kind="PURCHASE", actor=self.order.customer, notes="Delivery")
        alert = StockAlert.objects.get(inventory_item=self.stock)
        self.assertFalse(alert.is_active)
        self.assertIsNotNone(alert.resolved_at)
