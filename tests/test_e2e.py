from datetime import date, time, timedelta
from decimal import Decimal
import os
import pytest
from playwright.sync_api import sync_playwright, expect
from apps.inventory.models import Recipe, RecipeIngredient
from apps.orders.models import Order
from apps.reservations.models import Reservation
from apps.restaurants.models import OperatingHours
from tests.factories import MenuItemFactory, TableFactory, UserFactory, InventoryFactory

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.e2e]


@pytest.fixture
def browser_page(live_server):
    from contextlib import contextmanager
    @contextmanager
    def open_browser():
        with sync_playwright() as playwright:
            options = {"headless": True}
            if os.getenv("PLAYWRIGHT_CHANNEL"):
                options["channel"] = os.environ["PLAYWRIGHT_CHANNEL"]
            browser = playwright.chromium.launch(**options)
            page = browser.new_page(viewport={"width": 1365, "height": 900})
            page.set_default_timeout(10000)
            page.set_default_navigation_timeout(15000)
            try:
                yield page
            finally:
                from pathlib import Path
                Path(".local/e2e").mkdir(parents=True, exist_ok=True)
                page.screenshot(path=".local/e2e/latest.png", full_page=True)
                Path(".local/e2e/latest.html").write_text(page.content(), encoding="utf-8")
                browser.close()
    return open_browser, live_server.url


def login(page, base, username, password="Test-password-835!"):
    page.goto(base + "/accounts/login/")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password:", exact=True).fill(password)
    page.get_by_role("button", name="Log in", exact=True).click()
    page.wait_for_url(base + "/")


def test_customer_registration_order_and_reservation(browser_page):
    open_browser, base = browser_page
    item = MenuItemFactory()
    table = TableFactory(branch=item.branch)
    tomorrow = date.today() + timedelta(days=2)
    OperatingHours.objects.create(branch=item.branch, weekday=tomorrow.weekday(), opens_at=time(8), closes_at=time(23))
    with open_browser() as page:
        page.goto(base + "/register/")
        page.get_by_label("Username").fill("browserguest")
        page.get_by_label("Email").fill("browserguest@example.com")
        page.get_by_label("Password:", exact=True).fill("Browser-password-835!")
        page.get_by_label("Password confirmation").fill("Browser-password-835!")
        page.get_by_role("button", name="Create account").click()
        page.wait_for_url(base + "/my/")
        page.goto(base + f"/cart/?item={item.pk}")
        page.get_by_role("button", name="Add to cart").click()
        page.wait_for_url(base + "/cart/")
        page.get_by_role("button", name="Place order").click()
        page.wait_for_url("**/orders/*/")
        expect(page.get_by_text("Thank you for your order")).to_be_visible()
        page.goto(base + "/reservations/")
        page.get_by_label("Location").select_option(str(item.branch_id))
        page.get_by_label("Date", exact=True).fill(str(tomorrow))
        page.get_by_label("Start time").fill("12:00")
        page.get_by_label("End time").fill("13:00")
        page.get_by_role("button", name="Find a table").click()
        page.get_by_role("button", name="Select table").click()
        page.get_by_role("button", name="Request reservation").click()
        page.wait_for_url(base + "/my/")
        expect(page.get_by_text("PENDING").first).to_be_visible()
    assert Order.objects.filter(customer__username="browserguest").count() == 1
    assert Reservation.objects.filter(customer__username="browserguest").count() == 1


def test_staff_order_kitchen_and_inventory_workflow(browser_page):
    from apps.orders.services import create_order
    from apps.payments.services import record_payment
    open_browser, base = browser_page
    item = MenuItemFactory()
    stock = InventoryFactory(branch=item.branch, quantity=Decimal("5"))
    recipe = Recipe.objects.create(menu_item=item)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=stock.ingredient, quantity="1")
    customer = UserFactory()
    manager = UserFactory(role="MANAGER")
    item.branch.managers.add(manager)
    order = create_order(customer=customer, branch=item.branch, items=[{"menu_item": item.pk, "quantity": 1}])
    record_payment(order=order, amount=order.total, method="CASH", reference="browser-payment", actor=manager)
    with open_browser() as page:
        login(page, base, manager.username)
        page.goto(base + "/staff/")
        page.get_by_role("button", name="Orders", exact=True).click()
        page.get_by_role("button", name="CONFIRMED", exact=True).click()
        page.get_by_role("button", name="PREPARING", exact=True).click()
        page.get_by_role("button", name="READY", exact=True).click()
        page.get_by_role("button", name="COMPLETED", exact=True).click()
        expect(page.get_by_text("COMPLETED", exact=True)).to_be_visible()
        page.get_by_role("button", name="Inventory", exact=True).click()
        expect(page.get_by_text(stock.ingredient.name, exact=True)).to_be_visible()
        page.set_viewport_size({"width":390,"height":844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    stock.refresh_from_db()
    order.refresh_from_db()
    assert stock.quantity == Decimal("4")
    assert order.status == "COMPLETED"
