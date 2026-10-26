import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.orders.services import create_order
from tests.factories import MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_order_listing_query_count_does_not_grow_per_item(api_client):
    user = UserFactory()
    item = MenuItemFactory()
    api_client.force_authenticate(user)
    for _ in range(2):
        create_order(
            customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
        )
    with CaptureQueriesContext(connection) as small:
        assert api_client.get("/api/v1/orders/").status_code == 200
    for _ in range(15):
        create_order(
            customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
        )
    with CaptureQueriesContext(connection) as large:
        assert api_client.get("/api/v1/orders/").status_code == 200
    assert len(large) <= len(small) + 1


def test_public_menu_render_avoids_per_item_restaurant_queries(api_client):
    first = MenuItemFactory()
    with CaptureQueriesContext(connection) as small:
        assert api_client.get("/menu/").status_code == 200
    for _ in range(15):
        MenuItemFactory(branch=first.branch, category=first.category)
    with CaptureQueriesContext(connection) as large:
        assert api_client.get("/menu/").status_code == 200
    assert len(large) <= len(small) + 1
