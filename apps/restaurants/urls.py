from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, BranchViewSet, StaffBranchViewSet
router = DefaultRouter()
router.register("restaurants", RestaurantViewSet)
router.register("branches", BranchViewSet)
router.register("staff-branches", StaffBranchViewSet, basename="staff-branch")
urlpatterns = router.urls
