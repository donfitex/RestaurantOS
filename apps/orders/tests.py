from decimal import Decimal
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from apps.common.exceptions import Conflict
from apps.restaurants.models import Restaurant, Branch
from apps.menu.models import MenuCategory, MenuItem
from .models import Order
from .services import create_order, transition_order


class OrderServiceTests(TestCase):
    def setUp(self):
        restaurant = Restaurant.objects.create(name="One")
        self.branch = Branch.objects.create(restaurant=restaurant, name="Central", tax_rate="0.075")
        category = MenuCategory.objects.create(restaurant=restaurant, name="Mains")
        self.item = MenuItem.objects.create(branch=self.branch, category=category, name="Rice", sku="rice", price="1000")
        self.user = get_user_model().objects.create_user(username="customer", email="customer@example.com")

    def place(self, **kwargs):
        return create_order(customer=self.user, branch=self.branch, items=[{"menu_item": self.item.pk, "quantity": 2}], **kwargs)

    def test_prices_tax_and_snapshot(self):
        order = self.place(discount=Decimal("100"))
        self.assertEqual(order.total, Decimal("2042.50"))
        self.item.price = "2000"
        self.item.save()
        self.assertEqual(order.items.get().unit_price, Decimal("1000"))

    def test_retry_does_not_duplicate(self):
        key = uuid4()
        first = self.place(request_key=key)
        self.assertEqual(first.pk, self.place(request_key=key).pk)
        self.assertEqual(Order.objects.count(), 1)
        with self.assertRaises(Conflict):
            self.place(request_key=key, notes="different")

    def test_invalid_order_rolls_back(self):
        with self.assertRaises(ValidationError):
            self.place(discount=Decimal("3000"))
        self.assertFalse(Order.objects.exists())

    def test_invalid_transition_rejected(self):
        with self.assertRaises(Conflict):
            transition_order(self.place(), "COMPLETED")
