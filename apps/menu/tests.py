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

    def test_menu_search_price_filter_and_pagination(self):
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Main")
        category = MenuCategory.objects.create(restaurant=restaurant, name="Mains")
        MenuItem.objects.create(branch=branch, category=category, name="Rice", price="2000", sku="rice")
        MenuItem.objects.create(branch=branch, category=category, name="Soup", price="500", sku="soup")
        response = self.client.get("/api/v1/menu/items/?search=rice&min_price=1000&ordering=price")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["name"], "Rice")
