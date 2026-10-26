from rest_framework import serializers
from .models import Restaurant, Branch, OperatingHours


class HoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingHours
        fields = ["weekday", "opens_at", "closes_at"]


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name", "description", "address", "phone", "email", "timezone", "currency"]


class BranchSerializer(serializers.ModelSerializer):
    operating_hours = HoursSerializer(many=True, read_only=True)

    class Meta:
        model = Branch
        fields = ["id", "restaurant", "name", "address", "phone", "tax_rate", "operating_hours"]
