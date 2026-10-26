from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import connection, connections

from apps.common.exceptions import Conflict
from apps.inventory.models import Recipe, RecipeIngredient
from apps.inventory.services import adjust_stock
from apps.orders.models import Order
from apps.orders.services import create_order, transition_order
from apps.payments.services import record_payment
from apps.reservations.models import Reservation
from apps.reservations.services import create_reservation
from apps.restaurants.models import OperatingHours
from tests.factories import InventoryFactory, MenuItemFactory, TableFactory, UserFactory

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.postgres,
    pytest.mark.skipif(
        connection.vendor != "postgresql", reason="Requires PostgreSQL row-level locking"
    ),
]


def race(*operations):
    barrier = Barrier(len(operations))

    def run(operation):
        connections.close_all()
        try:
            barrier.wait(timeout=15)
            return ("ok", operation())
        except Conflict as exc:
            return ("conflict", str(exc))
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(operations)) as pool:
        return list(pool.map(run, operations))


def test_same_table_concurrent_booking_only_one_succeeds():
    table = TableFactory()
    day = date(2030, 1, 1)
    OperatingHours.objects.create(
        branch=table.branch, weekday=day.weekday(), opens_at=time(9), closes_at=time(22)
    )
    users = [UserFactory(), UserFactory()]

    def book(user):
        return create_reservation(
            customer=user,
            table=table,
            reservation_date=day,
            start_time=time(12),
            end_time=time(13),
            guest_count=2,
        ).pk

    results = race(lambda: book(users[0]), lambda: book(users[1]))
    assert sorted(result[0] for result in results) == ["conflict", "ok"]
    assert Reservation.objects.count() == 1


def stock_orders():
    item = MenuItemFactory()
    stock = InventoryFactory(branch=item.branch, quantity=Decimal("5"))
    recipe = Recipe.objects.create(menu_item=item)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=stock.ingredient, quantity="2")
    orders = [
        create_order(
            customer=UserFactory(),
            branch=item.branch,
            items=[{"menu_item": item.pk, "quantity": 2}],
        )
        for _ in range(2)
    ]
    return stock, orders


def test_competing_confirmations_never_oversell():
    stock, orders = stock_orders()
    results = race(
        lambda: transition_order(orders[0], "CONFIRMED").pk,
        lambda: transition_order(orders[1], "CONFIRMED").pk,
    )
    assert sorted(result[0] for result in results) == ["conflict", "ok"]
    stock.refresh_from_db()
    assert stock.quantity == Decimal("1")
    assert stock.movements.count() == 1


def test_simultaneous_stock_updates_do_not_lose_changes():
    stock = InventoryFactory(quantity=Decimal("5"))
    actor = UserFactory()
    results = race(
        lambda: adjust_stock(inventory_item=stock, quantity="2", kind="PURCHASE", actor=actor).pk,
        lambda: adjust_stock(inventory_item=stock, quantity="-4", kind="WASTE", actor=actor).pk,
    )
    assert [result[0] for result in results] == ["ok", "ok"]
    stock.refresh_from_db()
    assert stock.quantity == Decimal("3")
    assert stock.movements.count() == 2


def test_concurrent_order_retry_creates_one_order():
    item = MenuItemFactory()
    user = UserFactory()
    key = uuid4()

    def place():
        return create_order(
            customer=user,
            branch=item.branch,
            items=[{"menu_item": item.pk, "quantity": 1}],
            request_key=key,
        ).pk

    results = race(place, place)
    assert results[0] == results[1]
    assert Order.objects.count() == 1


def test_concurrent_payment_records_cannot_overpay():
    item = MenuItemFactory()
    user = UserFactory()
    order = create_order(
        customer=user, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}]
    )

    def pay(reference):
        return record_payment(
            order=order, amount=order.total, method="CASH", reference=reference, actor=user
        ).pk

    results = race(lambda: pay("one"), lambda: pay("two"))
    assert sorted(result[0] for result in results) == ["conflict", "ok"]
    assert order.payments.count() == 1


def test_customer_cancellation_cannot_cancel_a_concurrently_confirmed_order():
    stock, orders = stock_orders()
    order = orders[0]
    results = race(
        lambda: transition_order(order, "CONFIRMED").pk,
        lambda: transition_order(order, "CANCELLED", allowed_current={"PENDING"}).pk,
    )
    assert sorted(result[0] for result in results) == ["conflict", "ok"]
    order.refresh_from_db()
    stock.refresh_from_db()
    assert (order.status, stock.quantity) in [
        ("CONFIRMED", Decimal("1")),
        ("CANCELLED", Decimal("5")),
    ]


def test_same_payment_reference_across_orders_returns_conflict():
    item = MenuItemFactory()
    actor = UserFactory()
    orders = [
        create_order(
            customer=UserFactory(),
            branch=item.branch,
            items=[{"menu_item": item.pk, "quantity": 1}],
        )
        for _ in range(2)
    ]

    def pay(order):
        return record_payment(
            order=order,
            amount=order.total,
            method="CASH",
            reference="shared-reference",
            actor=actor,
        ).pk

    results = race(lambda: pay(orders[0]), lambda: pay(orders[1]))
    assert sorted(result[0] for result in results) == ["conflict", "ok"]


def test_same_order_request_key_across_users_returns_conflict():
    items = [MenuItemFactory(), MenuItemFactory()]
    users = [UserFactory(), UserFactory()]
    key = uuid4()

    def place(index):
        return create_order(
            customer=users[index],
            branch=items[index].branch,
            items=[{"menu_item": items[index].pk, "quantity": 1}],
            request_key=key,
        ).pk

    results = race(lambda: place(0), lambda: place(1))
    assert sorted(result[0] for result in results) == ["conflict", "ok"]
