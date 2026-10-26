import pytest

from apps.orders.services import create_order
from tests.factories import BranchFactory, InventoryFactory, MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        "/api/v1/orders/",
        "/api/v1/reservations/",
        "/api/v1/inventory/",
        "/api/v1/payments/",
        "/api/v1/auth/profile/",
        "/api/v1/tables/",
    ],
)
def test_private_apis_require_authentication(api_client, url):
    assert api_client.get(url).status_code == 403


@pytest.mark.parametrize(
    "role,inventory_allowed,orders_allowed",
    [
        ("MANAGER", True, True),
        ("INVENTORY_MANAGER", True, False),
        ("KITCHEN", False, True),
        ("WAITER", False, True),
        ("CASHIER", False, True),
        ("CUSTOMER", False, True),
    ],
)
def test_role_permission_matrix(api_client, role, inventory_allowed, orders_allowed):
    user = UserFactory(role=role)
    api_client.force_authenticate(user)
    assert (api_client.get("/api/v1/inventory/").status_code == 200) is inventory_allowed
    assert (api_client.get("/api/v1/orders/").status_code == 200) is orders_allowed


@pytest.mark.parametrize("quantity", [0, -1, 101, "bad"])
def test_order_quantity_validation(api_client, quantity):
    user = UserFactory()
    item = MenuItemFactory()
    api_client.force_authenticate(user)
    response = api_client.post(
        "/api/v1/orders/",
        {"branch": item.branch_id, "items": [{"menu_item": item.pk, "quantity": quantity}]},
        format="json",
    )
    assert response.status_code == 400


def test_staff_cannot_mutate_cross_branch_stock(api_client):
    user = UserFactory(role="INVENTORY_MANAGER")
    own = BranchFactory()
    own.staff.add(user)
    other = InventoryFactory()
    api_client.force_authenticate(user)
    assert (
        api_client.post(
            "/api/v1/inventory/adjust/",
            {"inventory_item": other.pk, "quantity": "10", "notes": "Attempt"},
        ).status_code
        == 404
    )


def test_menu_branch_price_filter_and_pagination(api_client):
    first = MenuItemFactory(price="100")
    MenuItemFactory(price="300")
    response = api_client.get(
        f"/api/v1/menu/items/?branch={first.branch_id}&min_price=50&max_price=150&ordering=-price"
    )
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == first.pk
    assert "next" in response.data


@pytest.mark.parametrize("target", [[], {}, None, "UNKNOWN"])
def test_invalid_status_payload_is_validation_error(api_client, target):
    user = UserFactory(role="ADMIN")
    item = MenuItemFactory()
    order = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    api_client.force_authenticate(user)
    response = api_client.patch(f"/api/v1/orders/{order.pk}/", {"status": target}, format="json")
    assert response.status_code == 400


def test_customer_cannot_self_settle_payment(api_client):
    user = UserFactory()
    api_client.force_authenticate(user)
    assert (
        api_client.post(
            "/api/v1/payments/",
            {"order": 1, "amount": "100", "method": "CASH", "reference": "fake"},
        ).status_code
        == 403
    )
