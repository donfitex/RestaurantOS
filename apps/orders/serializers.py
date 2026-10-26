from rest_framework import serializers

from apps.restaurants.models import Branch
from apps.tables.models import Table

from .models import Order, OrderItem, OrderModifier


class OrderModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderModifier
        fields = ["modifier", "name", "price"]


class OrderItemSerializer(serializers.ModelSerializer):
    modifiers = OrderModifierSerializer(many=True, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "menu_item",
            "name",
            "quantity",
            "unit_price",
            "subtotal",
            "notes",
            "modifiers",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "branch",
            "customer",
            "table",
            "order_type",
            "status",
            "subtotal",
            "tax",
            "discount",
            "total",
            "currency",
            "notes",
            "delivery_address",
            "request_key",
            "priority",
            "created_at",
            "confirmed_at",
            "preparing_at",
            "ready_at",
            "completed_at",
            "items",
        ]
        read_only_fields = fields


class OrderLineInput(serializers.Serializer):
    menu_item = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    modifiers = serializers.ListField(
        child=serializers.IntegerField(min_value=1), default=list, max_length=30
    )
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.filter(is_active=True))
    table = serializers.PrimaryKeyRelatedField(
        queryset=Table.objects.filter(is_active=True), required=False, allow_null=True
    )
    order_type = serializers.ChoiceField(choices=Order.Type.choices, default=Order.Type.TAKEAWAY)
    items = OrderLineInput(many=True, allow_empty=False)
    notes = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    delivery_address = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    discount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False
    )
    request_key = serializers.UUIDField(required=False)
