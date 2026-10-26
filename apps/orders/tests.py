from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import Conflict
from apps.menu.models import MenuCategory, MenuItem
from apps.restaurants.models import Branch, Restaurant

from .models import Order
from .services import create_order, transition_order


class OrderServiceTests(TestCase):
    def setUp(self):
        restaurant = Restaurant.objects.create(name="One")
        self.branch = Branch.objects.create(restaurant=restaurant, name="Central", tax_rate="0.075")
        category = MenuCategory.objects.create(restaurant=restaurant, name="Mains")
        self.item = MenuItem.objects.create(
            branch=self.branch, category=category, name="Rice", sku="rice", price="1000"
        )
        self.user = get_user_model().objects.create_user(
            username="customer", email="customer@example.com"
        )

    def place(self, **kwargs):
        return create_order(
            customer=self.user,
            branch=self.branch,
            items=[{"menu_item": self.item.pk, "quantity": 2}],
            **kwargs,
        )

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

    def test_api_rejects_customer_discount_and_cross_customer_access(self):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(self.user)
        payload = {
            "branch": self.branch.pk,
            "items": [{"menu_item": self.item.pk, "quantity": 1}],
            "discount": "10",
        }
        self.assertEqual(client.post("/api/v1/orders/", payload, format="json").status_code, 403)
        payload.pop("discount")
        response = client.post("/api/v1/orders/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        other = get_user_model().objects.create_user(username="other", email="other@example.com")
        client.force_authenticate(other)
        self.assertEqual(client.get(f"/api/v1/orders/{response.data['id']}/").status_code, 404)

    def test_kitchen_roles_and_preparation_timestamps(self):
        from rest_framework.test import APIClient

        order = transition_order(self.place(), "CONFIRMED")
        kitchen = get_user_model().objects.create_user(
            username="chef", email="chef@example.com", role="KITCHEN"
        )
        self.branch.staff.add(kitchen)
        client = APIClient()
        client.force_authenticate(kitchen)
        self.assertEqual(client.get("/api/v1/orders/kitchen/").data["count"], 1)
        self.assertEqual(
            client.patch(f"/api/v1/orders/{order.pk}/", {"status": "PREPARING"}).status_code, 200
        )
        self.assertEqual(
            client.patch(f"/api/v1/orders/{order.pk}/", {"status": "READY"}).status_code, 200
        )
        self.assertEqual(
            client.patch(f"/api/v1/orders/{order.pk}/", {"status": "COMPLETED"}).status_code, 403
        )
        order.refresh_from_db()
        self.assertIsNotNone(order.preparing_at)
        self.assertIsNotNone(order.ready_at)
        client.force_authenticate(self.user)
        self.assertEqual(client.get("/api/v1/orders/kitchen/").status_code, 403)
