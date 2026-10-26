from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PublicTableView, TableViewSet

router = DefaultRouter()
router.register("tables", TableViewSet)
urlpatterns = [path("public-tables/", PublicTableView.as_view())] + router.urls
