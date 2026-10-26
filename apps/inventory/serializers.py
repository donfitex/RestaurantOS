from rest_framework import serializers
from .models import InventoryItem, StockMovement


class InventorySerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)
    unit = serializers.CharField(source="ingredient.unit", read_only=True)
    minimum_stock = serializers.DecimalField(source="ingredient.minimum_stock", max_digits=14, decimal_places=3, read_only=True)

    class Meta:
        model = InventoryItem
        fields = ["id", "branch", "ingredient", "ingredient_name", "unit", "quantity", "minimum_stock", "updated_at"]
        read_only_fields = fields


class MovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id", "inventory_item", "kind", "quantity", "balance_after", "order", "actor", "reference", "notes", "created_at"]
        read_only_fields = fields


class AdjustmentSerializer(serializers.Serializer):
    inventory_item = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3)
    kind = serializers.ChoiceField(choices=["ADJUSTMENT", "WASTE"], default="ADJUSTMENT")
    notes = serializers.CharField(max_length=2000, allow_blank=False)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True)
