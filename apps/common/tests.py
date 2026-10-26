from django.test import TestCase


class PublicInterfaceTests(TestCase):
    def test_public_pages_render(self):
        for path in ["/", "/menu/", "/accounts/login/", "/register/", "/accounts/password_reset/", "/cart/"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get("/my/").status_code, 302)

    def test_reservation_interface_requires_login(self):
        self.assertEqual(self.client.get("/reservations/").status_code, 302)
