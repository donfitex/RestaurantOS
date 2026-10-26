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
