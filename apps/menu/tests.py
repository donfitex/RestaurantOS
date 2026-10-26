from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.restaurants.models import Restaurant, Branch
from .models import MenuCategory, MenuItem


class MenuTests(TestCase):
    def test_category_cannot_cross_restaurants(self):
        first = Restaurant.objects.create(name="One")
        second = Restaurant.objects.create(name="Two")
        branch = Branch.objects.create(restaurant=first, name="Central")
        category = MenuCategory.objects.create(restaurant=second, name="Mains")
        item = MenuItem(branch=branch, category=category, name="Rice", price=Decimal("2000"), sku="rice")
        with self.assertRaises(ValidationError):
            item.full_clean()
