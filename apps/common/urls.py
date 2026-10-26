from django.urls import path
from . import views
urlpatterns = [path("", views.home, name="home"), path("menu/", views.menu, name="menu"), path("menu/<int:pk>/", views.menu_detail, name="menu_detail"), path("register/", views.register, name="register"), path("my/", views.customer_dashboard, name="customer_dashboard")]
