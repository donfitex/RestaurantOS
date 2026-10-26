# API v1

Open `/api/docs/` for self-hosted interactive documentation and `/api/schema/` for OpenAPI. The checked-in openapi.yaml is generated with `python manage.py spectacular --settings=config.testing_postgres --file docs/openapi.yaml --validate --fail-on-warn`.

Authentication: GET /api/v1/auth/login/ obtains a CSRF cookie/token. POST the username/password with the X-CSRFToken header and retain the session cookie. Unsafe authenticated requests require CSRF. Session failures return 403. Validation returns 400, scoped missing objects 404, conflicting workflow/stock 409, and rate limits 429. Responses use JSON. Model lists return count, next, previous, results; default page size is 25.

Public: GET restaurants/, branches/, menu/, menu/categories/, menu/items/, menu/items/{id}/ and public-tables/?branch={id} under /api/v1/. Menu supports search, branch, category, min_price, max_price, availability, ordering=name|price|preparation_time and page.

Accounts: auth/register/, auth/login/, auth/logout/, auth/profile/ (GET/PATCH), auth/history/. Password reset uses the web flow /accounts/password_reset/. Public registration always creates a customer. Staff and customer directories are administrator-only.

Orders: POST orders/ with branch, order_type, items [{menu_item, quantity, modifiers, notes}], optional request_key UUID, notes, table, delivery_address. Managers may supply discount. Prices, tax, and totals are calculated by the server. Retry the same request_key only with an identical payload. PATCH orders/{id}/ with status. POST orders/{id}/cancel/. GET orders/kitchen/ defaults to active confirmed/preparing/ready orders; pass status=COMPLETED for completed history. Branch filtering is applied. It is restricted to kitchen/manager roles; managers POST orders/{id}/prioritize/ with priority 0?10.

Reservations: GET reservations/availability/ with branch, reservation_date, start_time, end_time, guest_count. POST reservations/ with branch, table and those slot fields plus optional guest_name, guest_phone, special_requests. PATCH reservations/{id}/ supports staff status changes. Customers cancel through POST reservations/{id}/cancel/ and rebook to change a slot. Time slots must fit published operating hours and begin in the future.

Inventory: GET inventory/, inventory/{id}/, inventory/{id}/movements/, inventory/low-stock/. POST inventory/restock/ or inventory/adjust/ with inventory_item, signed quantity, notes, optional reference. Restock requires positive quantity. Adjustment kind may be ADJUSTMENT or WASTE (negative). Inventory writes require manager/inventory-manager role and branch membership. Recipes and inventory records are configured in Django admin.

Payments: GET payments/ and payments/{id}/. Cashier/manager POST payments/ with order, amount, method, reference after verifying actual receipt of funds. Manager POST payments/{id}/refund/ with amount, reference, reason after verifying the external refund. Customers can read their own payments but cannot record settlement. Payment and refund references are unique and retry-safe for the same transaction.

Reports: GET reports/dashboard/?branch={id}. GET reports/operations/?branch={id}&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&period=day|week|month. Manager/admin only; maximum range 366 days. Sales-by-item/category reports use completed order values; dashboard sales use recorded net payments. Each report is restricted to a single branch/currency.

Staff branch membership scopes all operational resources. A record outside your scope returns 404 even if its id exists. Table management uses GET/POST/PATCH tables/ endpoints; physical deletion is disabled. Configuration and catalog changes use the administrator panel.
