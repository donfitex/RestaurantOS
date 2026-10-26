from datetime import timedelta
from unittest.mock import patch

import pytest
from django.db import OperationalError
from django.test import override_settings
from django.utils import timezone

from apps.common.models import AuditEvent, WorkerHeartbeat
from apps.orders.services import create_order
from tests.factories import MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_readiness_and_liveness(api_client):
    assert api_client.get("/health/").status_code == 200
    assert api_client.get("/health/live/").status_code == 200
    assert "X-Request-ID" in api_client.get("/health/")


@override_settings(REQUIRE_NOTIFICATION_WORKER=True)
def test_missing_or_stale_worker_is_unhealthy(api_client):
    assert api_client.get("/health/").status_code == 503
    WorkerHeartbeat.objects.create(name="notifications", last_seen_at=timezone.now())
    assert api_client.get("/health/").status_code == 200
    WorkerHeartbeat.objects.filter(name="notifications").update(
        last_seen_at=timezone.now() - timedelta(minutes=5)
    )
    assert api_client.get("/health/").status_code == 503


def test_database_failure_returns_safe_503(api_client):
    with patch(
        "apps.common.health.connection.cursor",
        side_effect=OperationalError("sensitive connection info"),
    ):
        response = api_client.get("/health/")
    assert response.status_code == 503
    assert b"sensitive" not in response.content


def test_order_creation_has_transactional_audit_record():
    item = MenuItemFactory()
    user = UserFactory()
    order = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    event = AuditEvent.objects.get(event="order.created", object_id=str(order.pk))
    assert event.actor_id == user.pk
    assert event.branch_id == item.branch_id


def test_logged_in_health_request_stays_safe_when_database_is_down(api_client):
    api_client.force_login(UserFactory())
    with patch("apps.common.health.connection.cursor", side_effect=OperationalError("private")):
        assert api_client.get("/health/").status_code == 503
