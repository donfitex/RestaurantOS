from rest_framework import serializers

from apps.common.scoping import staff_branches

from .models import Table


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = [
            "id",
            "branch",
            "table_number",
            "capacity",
            "location",
            "status",
            "is_active",
            "assigned_waiter",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if (
            branch
            and not staff_branches(self.context["request"].user).filter(pk=branch.pk).exists()
        ):
            raise serializers.ValidationError({"branch": "Branch access denied."})
        waiter = attrs.get("assigned_waiter")
        if waiter and (
            waiter.role != "WAITER" or not staff_branches(waiter).filter(pk=branch.pk).exists()
        ):
            raise serializers.ValidationError(
                {"assigned_waiter": "Choose a waiter assigned to this branch."}
            )
        if self.instance and branch.pk != self.instance.branch_id:
            raise serializers.ValidationError(
                {"branch": "Existing tables cannot move between branches."}
            )
        return attrs
