from django.contrib.auth import get_user_model
from django.test import TestCase


class AdministrationTests(TestCase):
    def test_all_domain_admin_lists_render(self):
        user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="test"
        )
        self.client.force_login(user)
        for path in [
            "users/user",
            "restaurants/restaurant",
            "restaurants/branch",
            "menu/menuitem",
            "tables/table",
            "reservations/reservation",
            "orders/order",
            "inventory/inventoryitem",
            "inventory/recipe",
            "inventory/stockmovement",
            "payments/payment",
        ]:
            self.assertEqual(self.client.get(f"/admin/{path}/").status_code, 200, path)
