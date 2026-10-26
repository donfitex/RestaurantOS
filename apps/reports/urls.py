from django.urls import path

from .views import DashboardView, OperationalReportView

urlpatterns = [
    path("operations/", OperationalReportView.as_view()),
    path("dashboard/", DashboardView.as_view()),
]
