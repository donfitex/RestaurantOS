import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import TimestampedModel


class Order(TimestampedModel):
    class Type(models.TextChoices):
        DINE_IN = "DINE_IN", "Dine in"
        TAKEAWAY = "TAKEAWAY", "Takeaway"
        DELIVERY = "DELIVERY", "Delivery"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PREPARING = "PREPARING", "Preparing"
        READY = "READY", "Ready"
        SERVED = "SERVED", "Served"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    branch = models.ForeignKey("restaurants.Branch", on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    table = models.ForeignKey("tables.Table", on_delete=models.PROTECT, null=True, blank=True, related_name="orders")
    order_type = models.CharField(max_length=10, choices=Type.choices, default=Type.TAKEAWAY)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3)
    notes = models.TextField(blank=True)
    delivery_address = models.TextField(blank=True)
    request_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    priority = models.PositiveSmallIntegerField(default=0)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    stock_deducted = models.BooleanField(default=False)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(subtotal__gte=0, tax__gte=0, discount__gte=0, total__gte=0), name="order_amounts_nonnegative"), models.CheckConstraint(condition=models.Q(total=models.F("subtotal") + models.F("tax") - models.F("discount")), name="order_total_consistent")]
        indexes = [models.Index(fields=["branch", "status", "created_at"]), models.Index(fields=["customer", "created_at"])]


class OrderItem(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.PROTECT)
    name = models.CharField(max_length=160)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0, unit_price__gte=0, subtotal__gte=0), name="order_item_positive"), models.CheckConstraint(condition=models.Q(subtotal=models.F("quantity") * models.F("unit_price")), name="order_item_total_consistent")]


class OrderModifier(TimestampedModel):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="modifiers")
    modifier = models.ForeignKey("menu.MenuModifier", on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["order_item", "modifier"], name="unique_order_item_modifier"), models.CheckConstraint(condition=models.Q(price__gte=0), name="order_modifier_nonnegative")]
