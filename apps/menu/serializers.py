from rest_framework import serializers
from .models import MenuCategory, MenuItem, MenuModifier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ["id", "restaurant", "name", "description"]


class ModifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuModifier
        fields = ["id", "name", "price"]


class MenuItemSerializer(serializers.ModelSerializer):
    modifiers = ModifierSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "branch", "category", "category_name", "name", "description", "price", "image", "sku", "availability", "preparation_time", "modifiers"]
