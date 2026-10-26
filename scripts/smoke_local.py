"""Verify the running loopback-only Docker demo through its actual HTTP/UI surfaces."""

import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode, urlparse
from uuid import uuid4
from zoneinfo import ZoneInfo

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def main():
    credentials = json.loads((ROOT / ".local/demo-credentials.json").read_text())
    base = credentials["url"]
    if urlparse(base).hostname not in ["localhost", "127.0.0.1"]:
        raise RuntimeError("This stateful smoke test is restricted to a local demo.")
    artifacts = ROOT / ".local/deployment"
    artifacts.mkdir(parents=True, exist_ok=True)
    report = {
        "url": base,
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    with sync_playwright() as playwright:
        options = {"headless": True}
        channel = os.getenv("PLAYWRIGHT_CHANNEL", "msedge" if sys.platform == "win32" else "")
        if channel:
            options["channel"] = channel
        browser = playwright.chromium.launch(**options)
        contexts = []

        def session(username):
            context = browser.new_context(viewport={"width": 1365, "height": 900})
            contexts.append(context)
            page = context.new_page()
            page.set_default_timeout(20000)
            page.goto(base + "/accounts/login/")
            page.get_by_label("Username").fill(username)
            page.get_by_label("Password:", exact=True).fill(credentials["password"])
            page.get_by_role("button", name="Log in", exact=True).click()
            page.wait_for_url(base + "/")
            return context, page

        def api(context, path, method="GET", payload=None):
            token = next(
                (
                    cookie["value"]
                    for cookie in context.cookies(base)
                    if cookie["name"] == "csrftoken"
                ),
                "",
            )
            response = context.request.fetch(
                base + path, method=method, data=payload, headers={"X-CSRFToken": token}
            )
            if response.status not in [200, 201, 204]:
                raise RuntimeError(f"{method} {path}: HTTP {response.status}")
            return response.json() if response.status != 204 else None

        admin, admin_page = session("admin")
        report["health"] = api(admin, "/health/")
        assert report["health"]["status"] == "healthy"
        assert api(admin, "/health/live/")["status"] == "alive"
        for path in [
            "/admin/",
            "/admin/orders/order/",
            "/admin/inventory/stockmovement/",
            "/admin/common/auditevent/",
        ]:
            assert admin.request.get(base + path).status == 200
        admin_page.goto(base + "/menu/")
        expect(
            admin_page.get_by_role("heading", name="Something for every appetite.")
        ).to_be_visible()
        admin_page.screenshot(path=str(artifacts / "menu-desktop.png"), full_page=True)
        admin_page.set_viewport_size({"width": 390, "height": 844})
        assert admin_page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        admin_page.screenshot(path=str(artifacts / "menu-mobile.png"), full_page=True)
        admin_page.set_viewport_size({"width": 1365, "height": 900})
        admin_page.goto(base + "/api/docs/")
        expect(admin_page.get_by_role("heading", name="RestaurantOS API")).to_be_visible()
        menu = api(admin, "/api/v1/menu/items/")
        assert menu["count"] >= 6
        item = menu["results"][0]
        manager, manager_page = session("manager")
        before = api(manager, "/api/v1/inventory/")["results"]
        customer, customer_page = session("customer")
        customer_page.goto(base + f"/cart/?item={item['id']}")
        customer_page.get_by_role("button", name="Add to cart").click()
        customer_page.wait_for_url(base + "/cart/")
        customer_page.get_by_role("button", name="Place order").click()
        customer_page.wait_for_url("**/orders/*/")
        order_id = int(re.search(r"/orders/(\d+)/", customer_page.url).group(1))
        order = api(customer, f"/api/v1/orders/{order_id}/")
        manager_page.goto(base + "/staff/")
        manager_page.get_by_role("button", name="Orders", exact=True).click()
        order_card = manager_page.locator("article").filter(has_text=f"Order #{order_id} ")
        for target in ["CONFIRMED", "PREPARING", "READY"]:
            order_card.get_by_role("button", name=target, exact=True).click()
        after = api(manager, "/api/v1/inventory/")["results"]
        original = {row["id"]: Decimal(row["quantity"]) for row in before}
        changed = [row for row in after if Decimal(row["quantity"]) < original[row["id"]]]
        assert changed, "Confirmation did not deduct stock"
        for row in changed:
            movements = api(manager, f"/api/v1/inventory/{row['id']}/movements/")["results"]
            assert any(
                movement["kind"] == "SALE" and movement["order"] == order_id
                for movement in movements
            )
        manager_page.get_by_role("button", name="Inventory", exact=True).click()
        sample_stock = changed[0]
        stock_card = manager_page.locator("article").filter(
            has=manager_page.get_by_role(
                "heading", name=sample_stock["ingredient_name"], exact=True
            )
        )
        for action, quantity, expected_quantity in [
            ("Restock", "1.000", Decimal(sample_stock["quantity"]) + 1),
            ("Adjust stock", "-1.000", Decimal(sample_stock["quantity"])),
        ]:
            answers = iter([quantity, "Local smoke inventory verification"])

            def answer(dialog, answers=answers):
                dialog.accept(next(answers))

            manager_page.on("dialog", answer)
            stock_card.get_by_role("button", name=action, exact=True).click()
            expect(
                stock_card.get_by_text(
                    f"{expected_quantity:.3f} {sample_stock['unit']}", exact=False
                )
            ).to_be_visible()
            manager_page.remove_listener("dialog", answer)
        stock_card.get_by_role("button", name="Movement history", exact=True).click()
        expect(
            stock_card.get_by_text("Local smoke inventory verification", exact=False).first
        ).to_be_visible()
        reference = "local-smoke-" + uuid4().hex
        manager_page.get_by_role("button", name="Payments", exact=True).click()
        manager_page.get_by_label("Order ID").fill(str(order_id))
        manager_page.get_by_label("Amount", exact=False).fill(order["total"])
        manager_page.get_by_label("Transaction reference").fill(reference)
        manager_page.get_by_label("Payment method").select_option("CASH")
        manager_page.get_by_role("button", name="Record payment", exact=True).click()
        expect(manager_page.get_by_text(reference, exact=False)).to_be_visible()
        manager_page.get_by_role("button", name="Orders", exact=True).click()
        order_card.get_by_role("button", name="COMPLETED", exact=True).click()
        expect(order_card.get_by_text("COMPLETED", exact=True)).to_be_visible()
        manager_page.screenshot(path=str(artifacts / "staff-desktop.png"), full_page=True)
        assert manager.request.get(base + f"/staff/receipts/{order_id}/").status == 200
        assert api(customer, f"/api/v1/orders/{order_id}/")["status"] == "COMPLETED"
        tomorrow = (datetime.now(ZoneInfo("Africa/Lagos")) + timedelta(days=2)).date()
        slot = {
            "branch": item["branch"],
            "reservation_date": str(tomorrow),
            "start_time": "13:00",
            "end_time": "14:00",
            "guest_count": 2,
        }
        available = api(customer, "/api/v1/reservations/availability/?" + urlencode(slot))
        assert available
        reservation = api(
            customer,
            "/api/v1/reservations/",
            "POST",
            {**slot, "table": available[0]["id"], "guest_name": "Local demo guest"},
        )
        reservation_id = reservation["id"]
        api(manager, f"/api/v1/reservations/{reservation_id}/", "PATCH", {"status": "CONFIRMED"})
        assert (
            api(customer, f"/api/v1/reservations/{reservation_id}/cancel/", "POST", {})["status"]
            == "CANCELLED"
        )
        assert any(
            table["id"] == available[0]["id"]
            for table in api(customer, "/api/v1/reservations/availability/?" + urlencode(slot))
        )
        dashboard = api(manager, f"/api/v1/reports/dashboard/?branch={item['branch']}")
        assert dashboard["orders"] >= 1
        day = datetime.now(ZoneInfo("Africa/Lagos")).date()
        operational = api(
            manager,
            "/api/v1/reports/operations/?"
            + urlencode({"branch": item["branch"], "start_date": str(day), "end_date": str(day)}),
        )
        assert operational["sales"]["by_item"]
        report.update(
            {
                "order_id": order_id,
                "order_status": "COMPLETED",
                "total": order["total"],
                "currency": order["currency"],
                "inventory_records_deducted": len(changed),
                "reservation_id": reservation_id,
                "reservation_status": "CANCELLED",
                "verified": [
                    "authentication",
                    "menu",
                    "checkout",
                    "kitchen",
                    "payment",
                    "receipt",
                    "stock_deduction",
                    "reservation",
                    "cancellation",
                    "dashboard",
                    "reports",
                    "admin",
                    "api_docs",
                    "health",
                    "responsive_menu",
                    "restock_and_adjustment",
                    "movement_history",
                ],
            }
        )
        for context in contexts:
            context.close()
        browser.close()
    (artifacts / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (ROOT / ".local/deployment-error.txt").write_text(traceback.format_exc())
        raise SystemExit(
            "Local smoke verification failed. Diagnostic saved in .local/deployment-error.txt."
        ) from None
