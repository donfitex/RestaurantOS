from decimal import Decimal

import pytest

from apps.common.exceptions import Conflict
from apps.common.models import Notification
from apps.inventory.models import Recipe, RecipeIngredient, StockMovement
from apps.inventory.services import adjust_stock
from apps.menu.models import MenuItemModifier, MenuModifier
from apps.orders.models import Order
from apps.orders.services import create_order, transition_order
from apps.payments.services import record_payment, refund_payment
from tests.factories import InventoryFactory, MenuItemFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_modifier_snapshot_and_tax_rounding():
    item = MenuItemFactory(price=Decimal("10.01"))
    modifier = MenuModifier.objects.create(
        restaurant=item.branch.restaurant, name="Extra", price="1.01"
    )
    MenuItemModifier.objects.create(menu_item=item, modifier=modifier)
    order = create_order(
        customer=UserFactory(),
        branch=item.branch,
        items=[{"menu_item": item.pk, "quantity": 3, "modifiers": [modifier.pk]}],
    )
    assert order.subtotal == Decimal("33.06")
    assert order.tax == Decimal("2.48")
    assert order.items.get().modifiers.get().price == Decimal("1.01")


def test_multi_ingredient_shortage_rolls_back_every_movement():
    item = MenuItemFactory()
    first = InventoryFactory(branch=item.branch, quantity=Decimal("5"))
    second = InventoryFactory(branch=item.branch, quantity=Decimal("0"))
    recipe = Recipe.objects.create(menu_item=item)
    for stock in [first, second]:
        RecipeIngredient.objects.create(recipe=recipe, ingredient=stock.ingredient, quantity="1")
    order = create_order(
        customer=UserFactory(), branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    with pytest.raises(Conflict):
        transition_order(order, "CONFIRMED")
    first.refresh_from_db()
    assert first.quantity == Decimal("5")
    assert not StockMovement.objects.exists()
    assert not Notification.objects.exists()


def test_stock_adjustment_never_goes_negative():
    stock = InventoryFactory(quantity=Decimal("2"))
    actor = UserFactory(role="INVENTORY_MANAGER")
    with pytest.raises(Conflict):
        adjust_stock(inventory_item=stock, quantity="-3", kind="WASTE", actor=actor)
    stock.refresh_from_db()
    assert stock.quantity == Decimal("2")
    assert not stock.movements.exists()


def test_refund_retry_does_not_double_refund():
    user = UserFactory()
    item = MenuItemFactory()
    order = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    payment = record_payment(
        order=order, amount=order.total, method="CASH", reference="payment-1", actor=user
    )
    first = refund_payment(
        payment=payment, amount="100", reference="refund-1", reason="Adjustment", actor=user
    )
    assert (
        refund_payment(
            payment=payment, amount="100", reference="refund-1", reason="Adjustment", actor=user
        ).pk
        == first.pk
    )
    payment.refresh_from_db()
    assert payment.refunded_amount == Decimal("100")


def test_unavailable_menu_item_creates_no_order():
    from rest_framework.exceptions import ValidationError

    item = MenuItemFactory(availability=False)
    with pytest.raises(ValidationError):
        create_order(
            customer=UserFactory(),
            branch=item.branch,
            items=[{"menu_item": item.pk, "quantity": 1}],
        )
    assert not Order.objects.exists()


def test_stock_ledger_records_the_confirming_staff_actor():
    item = MenuItemFactory()
    stock = InventoryFactory(branch=item.branch)
    recipe = Recipe.objects.create(menu_item=item)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=stock.ingredient, quantity="1")
    manager = UserFactory(role="MANAGER")
    order = create_order(
        customer=UserFactory(), branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )
    transition_order(order, "CONFIRMED", actor=manager)
    assert stock.movements.get(kind="SALE").actor_id == manager.pk
    transition_order(order, "CANCELLED", actor=manager)
    assert stock.movements.get(kind="RETURN").actor_id == manager.pk


def test_restock_cancels_pending_low_stock_emails():
    from apps.common.models import Notification
    from tests.factories import BranchFactory

    branch = BranchFactory()
    manager = UserFactory(role="MANAGER")
    branch.managers.add(manager)
    stock = InventoryFactory(branch=branch, quantity=Decimal("0"))
    assert Notification.objects.filter(status="PENDING").exists()
    adjust_stock(inventory_item=stock, quantity="10", kind="PURCHASE", actor=manager)
    assert not Notification.objects.filter(status="PENDING").exists()
    assert Notification.objects.filter(status="CANCELLED").exists()
