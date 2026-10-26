# Restaurant operations

## Configure a restaurant

An administrator creates the restaurant (timezone and currency), branches (tax rate), operating hours, menu categories and branch-specific menu items. Publish active items with positive/zero prices as appropriate. Add modifiers from the same restaurant. Images must be JPEG, PNG or WebP, within 5 MB and 20 million pixels.

Create tables with unique numbers per branch and suitable capacities. Assign staff to branches. Administrators manage catalog and staff configuration; managers run operations, discounts, reports and refunds. Waiters handle tables, reservations, confirmation and serving. Kitchen staff prepare and mark ready. Cashiers record verified payments and complete paid orders. Inventory managers restock and adjust inventory.

## Orders

Customers choose a branch menu, customize items, review the cart and place an order. The server recalculates all prices and snapshots them. Delivery requires an address; dine-in requires a table. Order requests begin PENDING. Staff confirm, prepare, mark READY, optionally SERVED, then COMPLETE once fully paid. Managers may prioritize the queue.

Confirmation deducts recipe quantities under database locks. Missing or insufficient branch stock prevents confirmation and rolls back all deductions. Menu items without recipes are untracked; configure a recipe for every item that should consume inventory. Repeated confirmation does not deduct again.

Customers may cancel only while PENDING. Staff cancellation is allowed before preparation. Recorded payments must be refunded first. Cancellation restores the recorded deductions once, even if the recipe changed. Preparing/ready/completed orders cannot be cancelled through this workflow; record operational waste/refunds as appropriate.

## Reservations and tables

Choose branch/date/start/end/guest count, check availability, then choose a suitable table. Reservations must fit the branch's published same-day operating interval. Overnight operating intervals are represented by separate dates/intervals in a future extension; the current configuration requires opening before closing on each weekday.

Bookings begin PENDING and block overlapping reservations. Adjacent slots are allowed. Staff confirm, seat, complete, or mark no-show. Seating requires an AVAILABLE physical table; completion marks it CLEANING. Staff return the table to AVAILABLE after cleaning. Cancellation releases the time slot. Table status is physical readiness, while future availability is calculated from reservation overlaps.

## Inventory

Ingredients define units and thresholds. Recipes use each ingredient's stock unit directly; automatic unit conversion is not performed. Example: use KG and 0.250 for 250 grams. Create an inventory record for each tracked ingredient/branch. Restock with positive quantities; adjustments use signed quantities and a reason; waste uses negative quantities. Every change records quantity, balance, actor and timestamp. Balances cannot go negative. Low-stock alerts activate at quantity <= minimum and resolve after restocking.

## Payments and reports

Record payment only after confirming actual receipt of money. Use unique transaction references. Refunds are manager-only and must reflect a real external refund. The application never collects card data or self-verifies customer payment claims. Receipts show item snapshots, totals and payment records.

Dashboard sales are net recorded payments for the branch-local date. Operational sales reports use completed order totals, with item/category breakdowns before tax and order-level discounts. Reports never combine currencies. Filter by branch and date range. Inventory movement totals are grouped by unit to avoid adding incompatible quantities.

## Notifications and audit

The separate notification worker delivers confirmation, cancellation, ready, payment and low-stock emails from a transactional outbox. Local mode prints email to the console. Configure SMTP in production. Failed deliveries retry with backoff, then remain FAILED after five attempts. SMTP is at least-once; an ambiguous delivery timeout may duplicate an email.

Django admin exposes read-only payment, stock movement, order, reservation and audit ledgers. Use /health/ for database/worker readiness, /health/live/ for process liveness. Monitor JSON request logs, latency, errors and the notification outbox.
