from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from apps.common.scoping import scope_branches
from apps.orders.models import Order
from apps.users.permissions import DomainPermission, is_admin
from .models import Payment
from .serializers import PaymentSerializer, PaymentInput, RefundInput
from .services import record_payment, refund_payment


class PaymentViewSet(ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related("order", "recorded_by").order_by("-created_at")
    serializer_class = PaymentSerializer
    permission_classes = [DomainPermission]
    read_roles = ("CUSTOMER", "CASHIER", "MANAGER")
    write_roles = ("CASHIER", "MANAGER")
    filterset_fields = ["order", "status", "method", "order__branch"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == "CUSTOMER" and not is_admin(self.request.user):
            return qs.filter(order__customer=self.request.user)
        return scope_branches(qs, self.request.user, "order__branch")

    def create(self, request):
        serializer = PaymentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        order = get_object_or_404(scope_branches(Order.objects.all(), request.user), pk=data.pop("order"))
        payment = record_payment(order=order, actor=request.user, **data)
        return Response(PaymentSerializer(payment).data, status=201)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        if request.user.role != "MANAGER" and not is_admin(request.user):
            raise PermissionDenied("Only managers may record refunds.")
        serializer = RefundInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = refund_payment(payment=self.get_object(), actor=request.user, **serializer.validated_data)
        return Response({"id": refund.pk, "amount": str(refund.amount), "reference": refund.reference}, status=201)
