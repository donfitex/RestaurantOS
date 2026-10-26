from rest_framework import serializers
from apps.restaurants.models import Branch
from apps.tables.models import Table
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "customer", "branch", "table", "guest_count", "reservation_date", "start_time", "end_time", "status", "special_requests", "guest_name", "guest_phone", "created_at"]
        read_only_fields = ["id", "customer", "status", "created_at"]

    def validate(self, attrs):
        if attrs["table"].branch_id != attrs["branch"].pk:
            raise serializers.ValidationError({"table": "Table does not belong to the selected branch."})
        return attrs


class AvailabilitySerializer(serializers.Serializer):
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.filter(is_active=True, restaurant__is_active=True))
    reservation_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    guest_count = serializers.IntegerField(min_value=1, max_value=100)
