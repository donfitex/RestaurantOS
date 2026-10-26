from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_registration_cannot_grant_staff_privileges(self):
        response = self.client.post("/api/v1/auth/register/", {"username": "customer", "email": "customer@example.com", "password": "Strong-password-835!", "role": "ADMIN", "is_superuser": True})
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username="customer")
        self.assertEqual(user.role, "CUSTOMER")
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password("Strong-password-835!"))

    def test_profile_cannot_change_role(self):
        user = get_user_model().objects.create_user(username="one", email="one@example.com", password="Strong-password-835!")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.patch("/api/v1/auth/profile/", {"role": "ADMIN"}).status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.role, "CUSTOMER")
        self.assertEqual(self.client.get("/api/v1/auth/staff/").status_code, 403)

    def test_login_requires_csrf(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/v1/auth/login/", {"username": "a", "password": "b"}).status_code, 403)

    def test_customer_history_is_personal(self):
        user = get_user_model().objects.create_user(username="history", email="history@example.com")
        self.client.force_authenticate(user)
        response = self.client.get("/api/v1/auth/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile"]["id"], user.pk)
        self.assertEqual(response.data["order_count"], 0)
        self.assertEqual(self.client.get("/api/v1/auth/customers/").status_code, 403)
