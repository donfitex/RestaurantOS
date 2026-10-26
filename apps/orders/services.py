import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from apps.common.exceptions import Conflict
from apps.menu.models import MenuItem
from apps.restaurants.models import Branch
from apps.tables.models import Table
from .models import Order, OrderItem, OrderModifier

CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


@transaction.atomic
def create_order(*, customer, branch, items, order_type="TAKEAWAY", table=None, notes="", delivery_address="", discount=Decimal("0"), request_key=None):
    if not items or len(items) > 100:
        raise ValidationError("Provide between one and 100 order lines.")
    payload = {"branch": branch.pk, "items": items, "type": order_type, "table": table.pk if table else None, "notes": notes, "address": delivery_address, "discount": str(discount)}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    get_user_model().objects.select_for_update().get(pk=customer.pk)
    if request_key:
        existing = Order.objects.filter(request_key=request_key).first()
        if existing:
            if existing.customer_id != customer.pk or existing.request_fingerprint != fingerprint:
                raise Conflict("Idempotency key was already used for a different request.")
            return existing
    branch = Branch.objects.select_related("restaurant").get(pk=branch.pk)
    if not branch.is_active or not branch.restaurant.is_active:
        raise ValidationError("Branch is unavailable.")
    if order_type not in Order.Type.values:
        raise ValidationError("Unknown order type.")
    if order_type == Order.Type.DELIVERY and not delivery_address.strip():
        raise ValidationError("Delivery address is required.")
    if order_type == Order.Type.DINE_IN and table is None:
        raise ValidationError("Dine-in orders require a table.")
    if table:
        table = Table.objects.select_for_update().get(pk=table.pk)
        if table.branch_id != branch.pk or not table.is_active or table.status in ["OUT_OF_SERVICE", "CLEANING"]:
            raise ValidationError("Table is unavailable or belongs to another branch.")
    menu_ids = [line["menu_item"] for line in items]
    menu = {item.pk: item for item in MenuItem.objects.select_for_update().filter(pk__in=menu_ids).select_related("category").order_by("pk")}
    subtotal = Decimal("0")
    snapshots = []
    for line in items:
        item = menu.get(line["menu_item"])
        quantity = line["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            raise ValidationError("Quantities must be whole numbers between 1 and 100.")
        if item is None or item.branch_id != branch.pk or not item.is_active or not item.availability or not item.category.is_active:
            raise ValidationError("One or more menu items are unavailable for this branch.")
        modifier_ids = line.get("modifiers", [])
        if len(set(modifier_ids)) != len(modifier_ids):
            raise ValidationError("Duplicate modifiers are not allowed.")
        modifiers = list(item.modifiers.filter(pk__in=modifier_ids, is_active=True, restaurant=branch.restaurant))
        if len(modifiers) != len(modifier_ids):
            raise ValidationError("An invalid modifier was selected.")
        unit_price = money(item.price + sum((m.price for m in modifiers), Decimal("0")))
        line_total = money(unit_price * quantity)
        subtotal += line_total
        snapshots.append((item, quantity, unit_price, line_total, line.get("notes", ""), modifiers))
    discount = money(discount)
    if discount < 0 or discount > subtotal:
        raise ValidationError("Discount must be between zero and the subtotal.")
    tax = money((subtotal - discount) * branch.tax_rate)
    data = dict(branch=branch, customer=customer, table=table, order_type=order_type, notes=notes, delivery_address=delivery_address, subtotal=subtotal, discount=discount, tax=tax, total=subtotal + tax - discount, currency=branch.restaurant.currency, request_fingerprint=fingerprint)
    if request_key:
        data["request_key"] = request_key
    order = Order.objects.create(**data)
    for item, quantity, unit_price, line_total, line_notes, modifiers in snapshots:
        order_item = OrderItem.objects.create(order=order, menu_item=item, name=item.name, quantity=quantity, unit_price=unit_price, subtotal=line_total, notes=line_notes)
        OrderModifier.objects.bulk_create([OrderModifier(order_item=order_item, modifier=m, name=m.name, price=m.price) for m in modifiers])
    return order


@transaction.atomic
def transition_order(order, target, *, allowed_current=None):
    order = Order.objects.select_for_update().get(pk=order.pk)
    if allowed_current is not None and order.status not in allowed_current:
        raise Conflict("The order status changed; this operation is no longer allowed.")
    if order.status == target:
        return order
    transitions = {"PENDING": {"CONFIRMED", "CANCELLED"}, "CONFIRMED": {"PREPARING", "CANCELLED"}, "PREPARING": {"READY"}, "READY": {"SERVED", "COMPLETED"}, "SERVED": {"COMPLETED"}}
    if target not in transitions.get(order.status, set()):
        raise Conflict("Invalid order status transition.")
    from apps.inventory.services import deduct_order_stock, restore_order_stock
    if target == "CONFIRMED":
        deduct_order_stock(order)
    elif target == "CANCELLED":
        restore_order_stock(order)
    timestamp = {"CONFIRMED": "confirmed_at", "PREPARING": "preparing_at", "READY": "ready_at", "COMPLETED": "completed_at"}.get(target)
    order.status = target
    fields = ["status", "updated_at"]
    if timestamp:
        setattr(order, timestamp, timezone.now())
        fields.append(timestamp)
    order.save(update_fields=fields)
    if target in ["CONFIRMED", "READY", "CANCELLED"]:
        from apps.common.notifications import notify_order
        notify_order(order, target)
    return order
