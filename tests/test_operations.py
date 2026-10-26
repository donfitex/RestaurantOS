import pytest

from apps.orders.models import Order
from apps.orders.services import create_order, transition_order
from tests.factories import BranchFactory, MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_kitchen_active_queue_is_branch_filtered_and_not_hidden_by_history(api_client):
    manager = UserFactory(role="MANAGER")
    item = MenuItemFactory()
    item.branch.managers.add(manager)
    other_branch = BranchFactory(restaurant=item.branch.restaurant)
    other_branch.managers.add(manager)
    Order.objects.bulk_create(
        [
            Order(branch=item.branch, customer=manager, currency="NGN", status="COMPLETED")
            for _ in range(30)
        ]
    )
    own = Order.objects.create(
        branch=item.branch, customer=manager, currency="NGN", status="CONFIRMED"
    )
    Order.objects.create(branch=other_branch, customer=manager, currency="NGN", status="CONFIRMED")
    api_client.force_authenticate(manager)
    response = api_client.get(f"/api/v1/orders/kitchen/?branch={item.branch_id}")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == own.pk
    history = api_client.get(f"/api/v1/orders/kitchen/?branch={item.branch_id}&status=COMPLETED")
    assert history.data["count"] == 30


def test_prioritizing_takeaway_order_does_not_lock_nullable_table_join(api_client):
    manager = UserFactory(role="MANAGER")
    item = MenuItemFactory()
    item.branch.managers.add(manager)
    order = create_order(
        customer=UserFactory(), branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    api_client.force_authenticate(manager)
    response = api_client.post(
        f"/api/v1/orders/{order.pk}/prioritize/", {"priority": 3}, format="json"
    )
    assert response.status_code == 200
    assert response.data["priority"] == 3


def test_superuser_with_default_customer_role_has_full_staff_interface(api_client):
    user = UserFactory(is_superuser=True, is_staff=True)
    api_client.force_login(user)
    response = api_client.get("/staff/")
    assert response.status_code == 200
    assert b'data-role="ADMIN"' in response.content
    item = MenuItemFactory()
    order = create_order(
        customer=UserFactory(), branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    transition_order(order, "CONFIRMED")
    api_client.force_authenticate(user)
    assert (
        api_client.post(f"/api/v1/orders/{order.pk}/cancel/", {}, format="json").status_code == 200
    )
