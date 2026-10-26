from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.restaurants.models import Restaurant, Branch
from apps.orders.models import Order
from apps.common.exceptions import Conflict
from .services import record_payment, refund_payment


class PaymentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cashier", email="cashier@example.com", role="CASHIER")
        restaurant = Restaurant.objects.create(name="One")
        branch = Branch.objects.create(restaurant=restaurant, name="Central")
        self.order = Order.objects.create(branch=branch, customer=self.user, subtotal="100", total="100", currency="NGN")

    def test_payment_and_refund_limits_and_retries(self):
        payment = record_payment(order=self.order, amount="100", method="CASH", reference="cash-1", actor=self.user)
        self.assertEqual(record_payment(order=self.order, amount="100", method="CASH", reference="cash-1", actor=self.user).pk, payment.pk)
        with self.assertRaises(Conflict):
            record_payment(order=self.order, amount="1", method="CASH", reference="cash-2", actor=self.user)
        refund_payment(payment=payment, amount="30", reference="refund-1", reason="Return", actor=self.user)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "PARTIALLY_REFUNDED")
        with self.assertRaises(Conflict):
            refund_payment(payment=payment, amount="71", reference="refund-2", reason="Return", actor=self.user)
        self.assertEqual(payment.refunded_amount, Decimal("30"))
