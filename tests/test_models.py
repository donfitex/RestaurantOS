from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.inventory.models import InventoryItem, Recipe, RecipeIngredient
from apps.orders.models import Order, OrderItem
from apps.payments.models import Payment
from tests.factories import (
    BranchFactory,
    IngredientFactory,
    InventoryFactory,
    MenuItemFactory,
    TableFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def test_factory_relationships_share_restaurant():
    item = MenuItemFactory()
    item.full_clean()
    assert item.category.restaurant_id == item.branch.restaurant_id


@pytest.mark.parametrize("capacity", [0, -1])
def test_table_capacity_database_constraint(capacity):
    with pytest.raises(IntegrityError), transaction.atomic():
        TableFactory(capacity=capacity)


def test_inventory_unique_per_branch_ingredient():
    stock = InventoryFactory()
    with pytest.raises(IntegrityError), transaction.atomic():
        InventoryItem.objects.create(branch=stock.branch, ingredient=stock.ingredient)


def test_order_total_database_constraint():
    with pytest.raises(IntegrityError), transaction.atomic():
        Order.objects.create(
            branch=BranchFactory(),
            customer=UserFactory(),
            currency="NGN",
            subtotal="100",
            total="99",
        )


def test_order_item_quantity_database_constraint():
    item = MenuItemFactory()
    order = Order.objects.create(branch=item.branch, customer=UserFactory(), currency="NGN")
    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(
            order=order, menu_item=item, name=item.name, quantity=0, unit_price="100", subtotal="0"
        )


def test_payment_refund_cannot_exceed_amount_in_database():
    user = UserFactory()
    order = Order.objects.create(branch=BranchFactory(), customer=user, currency="NGN")
    with pytest.raises(IntegrityError), transaction.atomic():
        Payment.objects.create(
            order=order,
            amount="10",
            refunded_amount="11",
            currency="NGN",
            method="CASH",
            reference="one",
            recorded_by=user,
        )


def test_recipe_model_rejects_cross_restaurant_ingredient():
    recipe = Recipe.objects.create(menu_item=MenuItemFactory())
    row = RecipeIngredient(recipe=recipe, ingredient=IngredientFactory(), quantity=Decimal("1"))
    with pytest.raises(ValidationError):
        row.full_clean()
