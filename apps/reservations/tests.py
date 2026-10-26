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
