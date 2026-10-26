from django.db import IntegrityError, transaction
from django.test import TestCase
from .models import Restaurant, Branch


class BranchTests(TestCase):
    def test_branch_names_unique_within_restaurant(self):
        restaurant = Restaurant.objects.create(name="Sample")
        Branch.objects.create(restaurant=restaurant, name="Central")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Branch.objects.create(restaurant=restaurant, name="Central")

    def test_inactive_branches_not_public(self):
        restaurant = Restaurant.objects.create(name="Sample")
        Branch.objects.create(restaurant=restaurant, name="Closed", is_active=False)
        self.assertEqual(self.client.get("/api/v1/branches/").json()["count"], 0)
