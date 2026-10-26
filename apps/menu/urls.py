from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("items", MenuItemViewSet)
urlpatterns = [path("", MenuItemViewSet.as_view({"get": "list"})), path("", include(router.urls))]
