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
