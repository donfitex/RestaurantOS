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
        return get_object_or_404(
            staff_branches(request.user).select_related("restaurant"), pk=int(raw)
        )


class DashboardView(BranchReportView):
    def get(self, request):
        return Response(daily_dashboard(self.branch(request)))


class OperationalReportView(BranchReportView):
    def get(self, request):
        from datetime import date

        from .selectors import operational_report

        branch = self.branch(request)
        try:
            start = date.fromisoformat(request.query_params.get("start_date", ""))
            end = date.fromisoformat(request.query_params.get("end_date", ""))
        except ValueError:
            raise ValidationError("Provide start_date and end_date in YYYY-MM-DD format.") from None
        if end < start or (end - start).days > 366:
            raise ValidationError("Report ranges must be ordered and no longer than 366 days.")
        period = request.query_params.get("period", "day")
        if period not in ["day", "week", "month"]:
            raise ValidationError({"period": "Choose day, week, or month."})
        return Response(operational_report(branch, start, end, period))
