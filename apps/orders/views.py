from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from apps.common.scoping import scope_branches, staff_branches
from apps.users.permissions import DomainPermission, is_admin
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import create_order, transition_order


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Order.objects.select_related("branch", "customer", "table").prefetch_related("items__modifiers").order_by("-created_at")
    serializer_class = OrderSerializer
    permission_classes = [DomainPermission]
    read_roles = ("CUSTOMER", "MANAGER", "WAITER", "CASHIER", "KITCHEN")
    write_roles = ("CUSTOMER", "MANAGER", "WAITER", "CASHIER", "KITCHEN")
    filterset_fields = ["branch", "status", "order_type"]
    search_fields = ["customer__username", "notes"]
    ordering_fields = ["created_at", "total", "priority"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        qs = super().get_queryset()
        if self.request.user.role == "CUSTOMER" and not is_admin(self.request.user):
            return qs.filter(customer=self.request.user)
        return scope_branches(qs, self.request.user)

    def create(self, request):
        if request.user.role == "KITCHEN" and not is_admin(request.user):
            raise PermissionDenied("Kitchen staff cannot place orders.")
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if request.user.role != "CUSTOMER" and not staff_branches(request.user).filter(pk=data["branch"].pk).exists():
            raise PermissionDenied("Branch access denied.")
        if data.get("discount", 0) and request.user.role != "MANAGER" and not is_admin(request.user):
            raise PermissionDenied("Only managers may grant discounts.")
        order = create_order(customer=request.user, **data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        if set(request.data) != {"status"}:
            raise ValidationError("Use this endpoint to update status only.")
        target = request.data["status"]
        if not isinstance(target, str) or target not in Order.Status.values:
            raise ValidationError({"status": "Choose a valid order status."})
        if not is_admin(request.user):
            allowed = {"MANAGER": {"CONFIRMED", "PREPARING", "READY", "SERVED", "COMPLETED", "CANCELLED"}, "WAITER": {"CONFIRMED", "SERVED"}, "CASHIER": {"CONFIRMED", "COMPLETED"}, "KITCHEN": {"PREPARING", "READY"}}
            if target not in allowed.get(request.user.role, set()):
                raise PermissionDenied("Your role cannot perform this transition.")
        return Response(OrderSerializer(transition_order(self.get_object(), target)).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if not is_admin(request.user) and request.user.role not in ["MANAGER", "CASHIER", "CUSTOMER"]:
            raise PermissionDenied("Your role cannot cancel orders.")
        if request.user.role == "CUSTOMER" and order.status != "PENDING":
            raise PermissionDenied("Only pending orders can be cancelled by customers.")
        return Response(OrderSerializer(transition_order(order, "CANCELLED", allowed_current={"PENDING"} if request.user.role == "CUSTOMER" and not is_admin(request.user) else None)).data)

    @action(detail=False, methods=["get"])
    def kitchen(self, request):
        if request.user.role not in ["KITCHEN", "MANAGER"] and not is_admin(request.user):
            raise PermissionDenied("Kitchen access is restricted to kitchen staff and managers.")
        queue = self.get_queryset().filter(status__in=["CONFIRMED", "PREPARING", "READY", "SERVED", "COMPLETED"]).order_by("-priority", "created_at")
        page = self.paginate_queryset(queue)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)

    @action(detail=True, methods=["post"])
    def prioritize(self, request, pk=None):
        if request.user.role != "MANAGER" and not is_admin(request.user):
            raise PermissionDenied("Only managers may change priority.")
        from django.db import transaction
        with transaction.atomic():
            order = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            value = request.data.get("priority")
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 10:
                raise ValidationError({"priority": "Use an integer from zero to ten."})
            order.priority = value
            order.save(update_fields=["priority", "updated_at"])
        return Response(OrderSerializer(order).data)
