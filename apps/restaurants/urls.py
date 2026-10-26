from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, BranchViewSet
router = DefaultRouter()
router.register("restaurants", RestaurantViewSet)
router.register("branches", BranchViewSet)
urlpatterns = router.urls
