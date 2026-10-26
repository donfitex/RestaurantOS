# Architecture

Each Django app owns its domain models and migrations. API serializers validate input and views authorize requests. Services own business transitions and transaction boundaries; selectors own reusable read queries. Models enforce storage invariants through database constraints.

Dependencies: restaurants -> menu/tables/inventory; users -> reservations/orders; menu -> recipes; orders -> inventory/payments. Shared models and errors live in common. Business workflows must call services rather than modifying statuses or balances directly.

Branch membership scopes staff operations. Customers can access their own orders and reservations. Only administrators provision staff identities. Monetary values use Decimal and order prices are snapshots. PostgreSQL row locks serialize mutations; SQLite supports local development only and does not verify concurrency guarantees.

Inventory deductions occur on confirmation, never on draft order creation. Cancellation restores recorded deductions once. Payments track externally verified transactions; this platform never treats customer-submitted payment data as settlement.
