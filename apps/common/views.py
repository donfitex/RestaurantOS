from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from apps.menu.models import MenuItem, MenuCategory, MenuModifier
from apps.restaurants.models import Branch
from .forms import CustomerRegistrationForm
from django.db.models import Prefetch


def home(request):
    return render(request, "public/home.html", {"branches": Branch.objects.filter(is_active=True, restaurant__is_active=True).select_related("restaurant")})


def menu(request):
    items = MenuItem.objects.filter(is_active=True, availability=True, category__is_active=True, branch__is_active=True, branch__restaurant__is_active=True).select_related("branch__restaurant", "category").prefetch_related(Prefetch("modifiers", queryset=MenuModifier.objects.filter(is_active=True)))
    search = request.GET.get("search", "").strip()
    if search:
        items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))
    for key in ["branch", "category"]:
        if request.GET.get(key, "").isdigit():
            items = items.filter(**{f"{key}_id": request.GET[key]})
    from django.core.paginator import Paginator
    return render(request, "public/menu.html", {"page": Paginator(items.order_by("name"), 24).get_page(request.GET.get("page")), "categories": MenuCategory.objects.filter(is_active=True, restaurant__is_active=True), "branches": Branch.objects.filter(is_active=True, restaurant__is_active=True), "search": search})


def menu_detail(request, pk):
    item = get_object_or_404(MenuItem.objects.select_related("branch__restaurant", "category").prefetch_related("modifiers"), pk=pk, is_active=True, category__is_active=True, branch__is_active=True, branch__restaurant__is_active=True)
    return render(request, "public/menu_detail.html", {"item": item})


def register(request):
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready.")
        return redirect("customer_dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def customer_dashboard(request):
    return render(request, "public/dashboard.html")


from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def cart(request):
    return render(request, "public/cart.html")


@login_required
def order_confirmation(request, pk):
    from apps.orders.models import Order
    order = get_object_or_404(Order, pk=pk, customer=request.user)
    return render(request, "public/order_confirmation.html", {"order": order})


@login_required
@ensure_csrf_cookie
def reservation_page(request):
    return render(request, "public/reservations.html")


@login_required
@ensure_csrf_cookie
def staff_dashboard(request):
    from django.core.exceptions import PermissionDenied
    if request.user.role == "CUSTOMER" and not request.user.is_superuser:
        raise PermissionDenied
    return render(request, "public/staff.html")


@login_required
def receipt(request, pk):
    from apps.orders.models import Order
    from .scoping import scope_branches
    from django.core.exceptions import PermissionDenied
    if request.user.role not in ["ADMIN", "MANAGER", "CASHIER"] and not request.user.is_superuser:
        raise PermissionDenied
    order = get_object_or_404(scope_branches(Order.objects.select_related("branch__restaurant", "customer").prefetch_related("items__modifiers", "payments"), request.user), pk=pk)
    return render(request, "public/receipt.html", {"order": order})
