from decimal import Decimal

from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "amount",
            "refunded_amount",
            "currency",
            "method",
            "status",
            "reference",
            "recorded_by",
            "paid_at",
            "created_at",
        ]
        read_only_fields = fields


class PaymentInput(serializers.Serializer):
    order = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    reference = serializers.CharField(max_length=120)


class RefundInput(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal("0.01"))
    reference = serializers.CharField(max_length=120)
    reason = serializers.CharField(max_length=2000)
