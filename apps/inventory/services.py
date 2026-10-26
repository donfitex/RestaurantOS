from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.common.exceptions import Conflict
from apps.menu.models import MenuItem

from .models import InventoryItem, Recipe, StockMovement


def apply_movement(stock, delta, kind, *, actor=None, order=None, notes="", reference=""):
    balance = stock.quantity + delta
    if balance < 0:
        raise Conflict(f"Insufficient stock for {stock.ingredient.name}.")
    if balance > Decimal("99999999999.999"):
        raise ValidationError("Stock balance exceeds the supported limit.")
    if delta == 0:
        raise ValidationError("Stock movements must have a nonzero quantity.")
    stock.quantity = balance
    stock.save(update_fields=["quantity", "updated_at"])
    movement = StockMovement.objects.create(
        inventory_item=stock,
        kind=kind,
        quantity=delta,
        balance_after=balance,
        actor=actor,
        order=order,
        notes=notes,
        reference=reference,
    )
    from apps.common.audit import record_event

    record_event(
        "inventory.movement",
        movement,
        actor=actor,
        branch=stock.branch,
        metadata={"kind": kind, "quantity": str(delta), "balance": str(balance)},
    )
    return movement


@transaction.atomic
def deduct_order_stock(order):
    if order.stock_deducted:
        return
    lines = list(order.items.all())
    list(
        MenuItem.objects.select_for_update()
        .filter(pk__in=[line.menu_item_id for line in lines])
        .order_by("pk")
    )
    recipes = {
        r.menu_item_id: r
        for r in Recipe.objects.filter(
            menu_item_id__in=[line.menu_item_id for line in lines]
        ).prefetch_related("ingredients__ingredient")
    }
    requirements = defaultdict(Decimal)
    for line in lines:
        recipe = recipes.get(line.menu_item_id)
        if recipe is None:
            continue
        for row in recipe.ingredients.all():
            if (
                row.ingredient.restaurant_id != order.branch.restaurant_id
                or not row.ingredient.is_active
            ):
                raise Conflict("Recipe contains an invalid ingredient.")
            requirements[row.ingredient_id] += row.quantity * line.quantity
    stocks = {
        s.ingredient_id: s
        for s in InventoryItem.objects.select_for_update()
        .select_related("ingredient")
        .filter(branch_id=order.branch_id, ingredient_id__in=requirements)
        .order_by("pk")
    }
    for ingredient_id, required in requirements.items():
        stock = stocks.get(ingredient_id)
        if stock is None:
            raise Conflict("Recipe ingredient has no inventory record at this branch.")
        apply_movement(stock, -required, StockMovement.Kind.SALE, order=order, actor=order.customer)
    order.stock_deducted = True
    order.save(update_fields=["stock_deducted", "updated_at"])


@transaction.atomic
def restore_order_stock(order):
    if not order.stock_deducted:
        return
    sales = list(
        order.stock_movements.filter(kind=StockMovement.Kind.SALE).order_by("inventory_item_id")
    )
    stocks = {
        s.pk: s
        for s in InventoryItem.objects.select_for_update()
        .select_related("ingredient")
        .filter(pk__in=[m.inventory_item_id for m in sales])
        .order_by("pk")
    }
    for movement in sales:
        apply_movement(
            stocks[movement.inventory_item_id],
            -movement.quantity,
            StockMovement.Kind.RETURN,
            order=order,
            actor=order.customer,
            notes="Order cancellation",
        )
    order.stock_deducted = False
    order.save(update_fields=["stock_deducted", "updated_at"])


@transaction.atomic
def adjust_stock(*, inventory_item, quantity, kind, actor, notes="", reference=""):
    stock = (
        InventoryItem.objects.select_for_update()
        .select_related("ingredient")
        .get(pk=inventory_item.pk)
    )
    delta = Decimal(str(quantity))
    if not delta.is_finite() or delta != delta.quantize(Decimal("0.001")):
        raise ValidationError("Use a finite quantity with at most three decimal places.")
    if kind == "PURCHASE" and delta <= 0:
        raise ValidationError("Restock quantities must be positive.")
    if kind == "WASTE" and delta >= 0:
        raise ValidationError("Waste quantities must be negative.")
    if kind not in ["PURCHASE", "WASTE", "ADJUSTMENT"]:
        raise ValidationError("Unsupported stock adjustment kind.")
    return apply_movement(stock, delta, kind, actor=actor, notes=notes, reference=reference)
