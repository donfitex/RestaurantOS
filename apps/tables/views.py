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
        return scope_branches(super().get_queryset(), self.request.user)
