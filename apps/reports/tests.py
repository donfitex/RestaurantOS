from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from apps.restaurants.models import Restaurant, Branch


class DashboardTests(TestCase):
    def test_dashboard_requires_branch_membership(self):
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Main")
        user = get_user_model().objects.create_user(username="manager", email="manager@example.com", role="MANAGER")
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get(f"/api/v1/reports/dashboard/?branch={branch.pk}").status_code, 404)
        branch.managers.add(user)
        response = client.get(f"/api/v1/reports/dashboard/?branch={branch.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["currency"], "NGN")
        self.assertEqual(response.data["orders"], 0)

        report = client.get(f"/api/v1/reports/operations/?branch={branch.pk}&start_date=2030-01-01&end_date=2030-01-31")
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["orders"], [])
        self.assertEqual(client.get(f"/api/v1/reports/operations/?branch={branch.pk}&start_date=2030-01-01&end_date=2032-01-31").status_code, 400)
