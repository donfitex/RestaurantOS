import django_filters
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import MenuCategory, MenuItem, MenuModifier
from .serializers import CategorySerializer, MenuItemSerializer
from django.db.models import Prefetch


class MenuFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = MenuItem
        fields = ["branch", "category", "availability"]


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = MenuCategory.objects.filter(is_active=True, restaurant__is_active=True).order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filterset_fields = ["restaurant"]
    search_fields = ["name"]


class MenuItemViewSet(ReadOnlyModelViewSet):
    queryset = MenuItem.objects.filter(is_active=True, category__is_active=True, branch__is_active=True, branch__restaurant__is_active=True).select_related("category", "branch").prefetch_related(Prefetch("modifiers", queryset=MenuModifier.objects.filter(is_active=True))).order_by("name")
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    filterset_class = MenuFilter
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["name", "price", "preparation_time"]
