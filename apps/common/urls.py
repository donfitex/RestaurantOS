from django.urls import path
from . import views
urlpatterns = [path("reservations/", views.reservation_page, name="reservation_page"), path("cart/", views.cart, name="cart"), path("orders/<int:pk>/", views.order_confirmation, name="order_confirmation"), path("", views.home, name="home"), path("menu/", views.menu, name="menu"), path("menu/<int:pk>/", views.menu_detail, name="menu_detail"), path("register/", views.register, name="register"), path("my/", views.customer_dashboard, name="customer_dashboard")]
