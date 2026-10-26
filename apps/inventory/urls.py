from rest_framework.routers import DefaultRouter

from .views import InventoryViewSet

router = DefaultRouter()
router.register("inventory", InventoryViewSet)
urlpatterns = router.urls
