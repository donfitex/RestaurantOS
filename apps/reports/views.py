from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.common.scoping import staff_branches
from apps.users.permissions import DomainPermission
from .selectors import daily_dashboard


class BranchReportView(APIView):
    permission_classes = [DomainPermission]
    read_roles = ("MANAGER",)
    write_roles = ()

    def branch(self, request):
        raw = request.query_params.get("branch", "")
        if not raw.isdigit():
            raise ValidationError({"branch": "Provide a branch id."})
        return get_object_or_404(staff_branches(request.user).select_related("restaurant"), pk=int(raw))


class DashboardView(BranchReportView):
    def get(self, request):
        return Response(daily_dashboard(self.branch(request)))
