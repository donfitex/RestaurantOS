from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.common.scoping import scope_branches, staff_branches
from apps.users.permissions import DomainPermission, is_admin

from .models import Reservation
from .serializers import AvailabilitySerializer, ReservationSerializer
from .services import available_tables, create_reservation, transition_reservation


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Reservation.objects.select_related("table", "branch", "customer").order_by(
        "-reservation_date", "start_time"
    )
    serializer_class = ReservationSerializer
    permission_classes = [DomainPermission]
    read_roles = write_roles = ("CUSTOMER", "MANAGER", "WAITER")
    filterset_fields = ["branch", "status", "reservation_date"]
    search_fields = ["guest_name", "guest_phone"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        queryset = super().get_queryset()
        if self.request.user.role == "CUSTOMER" and not is_admin(self.request.user):
            return queryset.filter(customer=self.request.user)
        return scope_branches(queryset, self.request.user)

    def perform_create(self, serializer):
        data = dict(serializer.validated_data)
        branch = data.pop("branch")
        if (
            self.request.user.role != "CUSTOMER"
            and not staff_branches(self.request.user).filter(pk=branch.pk).exists()
        ):
            raise PermissionDenied("Branch access denied.")
        serializer.instance = create_reservation(customer=self.request.user, **data)

    @action(detail=False, methods=["get"])
    def availability(self, request):
        serializer = AvailabilitySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        tables = available_tables(**serializer.validated_data)
        return Response(
            [
                {
                    "id": t.pk,
                    "table_number": t.table_number,
                    "capacity": t.capacity,
                    "location": t.location,
                }
                for t in tables
            ]
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return Response(
            self.get_serializer(transition_reservation(self.get_object(), "CANCELLED")).data
        )

    def partial_update(self, request, pk=None):
        reservation = self.get_object()
        if self.request.user.role == "CUSTOMER" and not is_admin(self.request.user):
            raise PermissionDenied("Customers can cancel using the cancel action.")
        if set(request.data) != {"status"}:
            raise ValidationError(
                "Only status changes are supported; cancel and rebook to change a slot."
            )
        target = request.data["status"]
        if not isinstance(target, str) or target not in Reservation.Status.values:
            raise ValidationError({"status": "Choose a valid reservation status."})
        return Response(self.get_serializer(transition_reservation(reservation, target)).data)
