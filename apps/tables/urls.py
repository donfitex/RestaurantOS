from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import TableViewSet, PublicTableView
router = DefaultRouter()
router.register("tables", TableViewSet)
urlpatterns = [path("public-tables/", PublicTableView.as_view())] + router.urls
