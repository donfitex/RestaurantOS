from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.scoping import scope_branches
from apps.users.permissions import DomainPermission

from .models import Table
from .serializers import TableSerializer


class TableViewSet(ModelViewSet):
    queryset = Table.objects.select_related("branch", "assigned_waiter").order_by("table_number")
    serializer_class = TableSerializer
    permission_classes = [DomainPermission]
    read_roles = ("MANAGER", "WAITER", "CASHIER")
    write_roles = ("MANAGER", "WAITER")
    filterset_fields = ["branch", "status", "is_active"]
    search_fields = ["table_number", "location"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return scope_branches(super().get_queryset(), self.request.user)


class PublicTableView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branch = request.query_params.get("branch", "")
        if not branch.isdigit():
            raise ValidationError({"branch": "Provide a branch id."})
        return Response(
            list(
                Table.objects.filter(
                    branch_id=branch,
                    branch__is_active=True,
                    branch__restaurant__is_active=True,
                    is_active=True,
                )
                .exclude(status="OUT_OF_SERVICE")
                .values("id", "table_number", "capacity", "status")
            )
        )
