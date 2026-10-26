from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.restaurants.models import Branch, Restaurant

from .models import Table


class TableScopeTests(TestCase):
    def test_staff_cannot_read_other_branch_tables(self):
        restaurant = Restaurant.objects.create(name="One")
        own = Branch.objects.create(restaurant=restaurant, name="Own")
        other = Branch.objects.create(restaurant=restaurant, name="Other")
        user = get_user_model().objects.create_user(
            username="waiter", email="waiter@example.com", role="WAITER"
        )
        own.staff.add(user)
        table = Table.objects.create(branch=other, table_number="1", capacity=4)
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get(f"/api/v1/tables/{table.pk}/").status_code, 404)
        self.assertEqual(
            client.post(
                "/api/v1/tables/", {"branch": other.pk, "table_number": "2", "capacity": 4}
            ).status_code,
            400,
        )
