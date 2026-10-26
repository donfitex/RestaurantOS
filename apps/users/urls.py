from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, LogoutView, ProfileView, StaffViewSet, CustomerViewSet, CustomerHistoryView
router = DefaultRouter()
router.register("staff", StaffViewSet)
router.register("customers", CustomerViewSet, basename="customer")
urlpatterns = [path("history/", CustomerHistoryView.as_view()), path("register/", RegisterView.as_view()), path("login/", LoginView.as_view()), path("logout/", LogoutView.as_view()), path("profile/", ProfileView.as_view()), path("", include(router.urls))]

