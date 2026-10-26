import pytest
from django.test import override_settings

from apps.common.exceptions import Conflict
from apps.orders.services import create_order, transition_order
from apps.payments.services import record_payment
from tests.factories import MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_security_headers(api_client):
    response = api_client.get("/")
    assert "script-src 'self'" in response["Content-Security-Policy"]
    assert response["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"


@override_settings(AUTH_RATE_LIMIT=2)
def test_login_attempts_are_database_rate_limited(api_client):
    for _ in range(2):
        assert (
            api_client.post(
                "/api/v1/auth/login/", {"username": "bad", "password": "bad"}
            ).status_code
            == 400
        )
    response = api_client.post("/api/v1/auth/login/", {"username": "bad", "password": "bad"})
    assert response.status_code == 429
    assert response["Retry-After"] == "60"


def test_completion_requires_payment_and_cancellation_requires_refund():
    user = UserFactory()
    item = MenuItemFactory()
    order = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    for target in ["CONFIRMED", "PREPARING", "READY"]:
        order = transition_order(order, target)
    with pytest.raises(Conflict):
        transition_order(order, "COMPLETED")
    record_payment(order=order, amount=order.total, method="CASH", reference="verified", actor=user)
    transition_order(order, "COMPLETED")
    pending = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    record_payment(
        order=pending, amount=pending.total, method="CASH", reference="another", actor=user
    )
    with pytest.raises(Conflict):
        transition_order(pending, "CANCELLED")
