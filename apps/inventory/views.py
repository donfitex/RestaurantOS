from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.common.scoping import scope_branches
from apps.users.permissions import DomainPermission

from .models import InventoryItem
from .serializers import AdjustmentSerializer, InventorySerializer, MovementSerializer
from .services import adjust_stock


class InventoryViewSet(ReadOnlyModelViewSet):
    queryset = InventoryItem.objects.select_related("branch", "ingredient").order_by(
        "ingredient__name"
    )
    serializer_class = InventorySerializer
    permission_classes = [DomainPermission]
    read_roles = write_roles = ("MANAGER", "INVENTORY_MANAGER")
    filterset_fields = ["branch", "ingredient"]
    search_fields = ["ingredient__name", "ingredient__sku"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return scope_branches(super().get_queryset(), self.request.user)

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        qs = self.filter_queryset(self.get_queryset()).filter(
            quantity__lte=F("ingredient__minimum_stock")
        )
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    def _adjust(self, request, restock=False):
        serializer = AdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        stock = get_object_or_404(self.get_queryset(), pk=data.pop("inventory_item"))
        if restock:
            data["kind"] = "PURCHASE"
        movement = adjust_stock(inventory_item=stock, actor=request.user, **data)
        return Response(MovementSerializer(movement).data, status=201)

    @action(detail=False, methods=["post"])
    def adjust(self, request):
        return self._adjust(request)

    @action(detail=False, methods=["post"])
    def restock(self, request):
        return self._adjust(request, restock=True)

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        qs = self.get_object().movements.select_related("actor", "order").order_by("-created_at")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(MovementSerializer(page, many=True).data)
