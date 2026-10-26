"""Explicit contracts for workflow endpoints whose payloads differ from model reads."""
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from apps.users.views import LoginView, LogoutView, CustomerHistoryView
from apps.users.serializers import ProfileSerializer
from apps.orders.views import OrderViewSet
from apps.orders.serializers import OrderCreateSerializer, OrderSerializer
from apps.reservations.views import ReservationViewSet
from apps.reservations.serializers import AvailabilitySerializer, ReservationSerializer
from apps.inventory.views import InventoryViewSet
from apps.inventory.serializers import AdjustmentSerializer, MovementSerializer
from apps.payments.views import PaymentViewSet
from apps.payments.serializers import PaymentInput, RefundInput, PaymentSerializer
from apps.tables.views import PublicTableView
from apps.reports.views import DashboardView, OperationalReportView

LoginInput = inline_serializer("LoginInput", fields={"username": serializers.CharField(), "password": serializers.CharField(write_only=True)})
StatusInput = inline_serializer("StatusInput", fields={"status": serializers.CharField()})
PriorityInput = inline_serializer("PriorityInput", fields={"priority": serializers.IntegerField(min_value=0, max_value=10)})
PublicTable = inline_serializer("PublicTable", fields={"id": serializers.IntegerField(), "table_number": serializers.CharField(), "capacity": serializers.IntegerField(), "status": serializers.CharField()}, many=True)

extend_schema_view(get=extend_schema(responses=OpenApiTypes.OBJECT), post=extend_schema(request=LoginInput, responses={200: ProfileSerializer, 400: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT}))(LoginView)
extend_schema_view(post=extend_schema(request=None, responses={204: None}))(LogoutView)
extend_schema_view(get=extend_schema(responses=OpenApiTypes.OBJECT))(CustomerHistoryView)
extend_schema_view(create=extend_schema(request=OrderCreateSerializer, responses={201: OrderSerializer, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT}), partial_update=extend_schema(request=StatusInput, responses=OrderSerializer), cancel=extend_schema(request=None, responses=OrderSerializer), prioritize=extend_schema(request=PriorityInput, responses=OrderSerializer), kitchen=extend_schema(responses=OrderSerializer(many=True)))(OrderViewSet)
extend_schema_view(availability=extend_schema(parameters=[AvailabilitySerializer], responses=PublicTable), partial_update=extend_schema(request=StatusInput, responses=ReservationSerializer), cancel=extend_schema(request=None, responses=ReservationSerializer))(ReservationViewSet)
extend_schema_view(adjust=extend_schema(request=AdjustmentSerializer, responses={201: MovementSerializer}), restock=extend_schema(request=AdjustmentSerializer, responses={201: MovementSerializer}), movements=extend_schema(responses=MovementSerializer(many=True)))(InventoryViewSet)
extend_schema_view(create=extend_schema(request=PaymentInput, responses={201: PaymentSerializer, 409: OpenApiTypes.OBJECT}), refund=extend_schema(request=RefundInput, responses={201: OpenApiTypes.OBJECT}))(PaymentViewSet)
extend_schema_view(get=extend_schema(parameters=[OpenApiParameter("branch", int, required=True)], responses=PublicTable))(PublicTableView)
extend_schema_view(get=extend_schema(parameters=[OpenApiParameter("branch", int, required=True)], responses=OpenApiTypes.OBJECT))(DashboardView)
extend_schema_view(get=extend_schema(parameters=[OpenApiParameter("branch", int, required=True), OpenApiParameter("start_date", OpenApiTypes.DATE, required=True), OpenApiParameter("end_date", OpenApiTypes.DATE, required=True), OpenApiParameter("period", str, enum=["day", "week", "month"])], responses=OpenApiTypes.OBJECT))(OperationalReportView)
