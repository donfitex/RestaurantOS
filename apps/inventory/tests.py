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
