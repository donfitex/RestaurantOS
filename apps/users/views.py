from django.contrib.auth import authenticate, login, logout, get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import AdministratorOnly
from .serializers import ProfileSerializer, RegistrationSerializer, StaffSerializer


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})

    def post(self, request):
        user = authenticate(request, username=request.data.get("username", ""), password=request.data.get("password", ""))
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response(ProfileSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class StaffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.exclude(role="CUSTOMER").order_by("id")
    serializer_class = StaffSerializer
    permission_classes = [AdministratorOnly]
    filterset_fields = ["role", "is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [AdministratorOnly]
    queryset = get_user_model().objects.filter(role="CUSTOMER").order_by("username")
    search_fields = ["username", "email", "phone"]


class CustomerHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.orders.models import Order
        from apps.reservations.models import Reservation
        from django.db.models import Sum
        from apps.payments.models import Payment
        orders = Order.objects.filter(customer=request.user)
        reservations = Reservation.objects.filter(customer=request.user)
        payments = Payment.objects.filter(order__customer=request.user, status__in=["PAID", "PARTIALLY_REFUNDED"])
        from django.db.models import F
        return Response({"profile": ProfileSerializer(request.user).data, "order_count": orders.count(), "reservation_count": reservations.count(), "net_paid": str(payments.aggregate(total=Sum(F("amount") - F("refunded_amount")))["total"] or 0), "orders_url": "/api/v1/orders/", "reservations_url": "/api/v1/reservations/", "payments_url": "/api/v1/payments/"})
