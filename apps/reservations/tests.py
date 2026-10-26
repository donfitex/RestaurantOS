from datetime import date, time
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.restaurants.models import Restaurant, Branch
from apps.tables.models import Table
from .models import Reservation


class ReservationModelTests(TestCase):
    def test_capacity_validation(self):
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Central")
        table = Table.objects.create(branch=branch, table_number="1", capacity=2)
        user = get_user_model().objects.create_user(username="guest", email="guest@example.com")
        reservation = Reservation(customer=user, branch=branch, table=table, guest_count=3, reservation_date=date(2030, 1, 1), start_time=time(12), end_time=time(13))
        with self.assertRaises(ValidationError):
            reservation.full_clean()


class AvailabilityTests(TestCase):
    def setUp(self):
        from apps.restaurants.models import OperatingHours
        self.restaurant = Restaurant.objects.create(name="One")
        self.branch = Branch.objects.create(restaurant=self.restaurant, name="Central")
        self.table = Table.objects.create(branch=self.branch, table_number="1", capacity=4)
        self.user = get_user_model().objects.create_user(username="guest", email="guest@example.com")
        self.day = date(2030, 1, 1)
        OperatingHours.objects.create(branch=self.branch, weekday=self.day.weekday(), opens_at=time(9), closes_at=time(22))

    def book(self, start=time(12), end=time(13)):
        from .services import create_reservation
        return create_reservation(customer=self.user, table=self.table, reservation_date=self.day, start_time=start, end_time=end, guest_count=2)

    def test_overlap_rejected_adjacent_allowed(self):
        from apps.common.exceptions import Conflict
        self.book()
        with self.assertRaises(Conflict):
            self.book(time(12, 30), time(13, 30))
        self.book(time(13), time(14))
        self.assertEqual(Reservation.objects.count(), 2)

    def test_cancellation_releases_slot(self):
        from .services import transition_reservation
        first = self.book()
        transition_reservation(first, "CANCELLED")
        self.book()
        self.assertEqual(Reservation.objects.count(), 2)

    def test_closed_hours_rejected(self):
        from rest_framework.exceptions import ValidationError as APIValidationError
        with self.assertRaises(APIValidationError):
            self.book(time(7), time(8))

    def test_api_ownership_and_duplicate_booking(self):
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(self.user)
        data = {"branch": self.branch.pk, "table": self.table.pk, "guest_count": 2, "reservation_date": str(self.day), "start_time": "12:00", "end_time": "13:00"}
        first = client.post("/api/v1/reservations/", data)
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(client.post("/api/v1/reservations/", data).status_code, 409)
        other = get_user_model().objects.create_user(username="other", email="other@example.com")
        client.force_authenticate(other)
        self.assertEqual(client.get(f"/api/v1/reservations/{first.data['id']}/").status_code, 404)
