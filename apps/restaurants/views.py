from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Restaurant, Branch
from .serializers import RestaurantSerializer, BranchSerializer


class RestaurantViewSet(ReadOnlyModelViewSet):
    queryset = Restaurant.objects.filter(is_active=True).order_by("name")
    serializer_class = RestaurantSerializer
    permission_classes = [AllowAny]


class BranchViewSet(ReadOnlyModelViewSet):
    queryset = Branch.objects.filter(is_active=True, restaurant__is_active=True).select_related("restaurant").prefetch_related("operating_hours").order_by("name")
    serializer_class = BranchSerializer
    permission_classes = [AllowAny]
    filterset_fields = ["restaurant"]
