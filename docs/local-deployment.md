# Verified local deployment

Verified on 2026-10-26 (Africa/Lagos) from application source revision df411748910db073f833308299a7fe63e21013cd.

URL: http://127.0.0.1:8000

Services: PostgreSQL 17, Gunicorn web application, separate notification worker. The one-shot migration service completed successfully. Readiness reported database=ok and notification_worker=ok. The web process runs as UID 999 with DEBUG=False and compressed manifest static storage.

The deployment is bound to loopback and uses config.local. Public HTTPS deployment has not been performed. Local email uses the console backend and payments are demo ledger entries, not external charges.

The real running deployment passed browser/HTTP smoke checks for:

- Administrator and customer/staff login.
- Public menu, responsive rendering and self-hosted API documentation.
- Customer cart checkout and order confirmation.
- Manager confirmation, preparation, ready state and completion.
- Recipe-based stock deduction.
- Staff payment entry through the UI and receipt rendering.
- Restocking, signed adjustments and visible movement history.
- Reservation availability, creation, staff confirmation and customer cancellation.
- Management dashboard and operational reports.
- Admin audit pages, process liveness and database/worker readiness.

The smoke order completed with its server-calculated total, and the cancelled reservation released its time slot. Screenshot and JSON artifacts are saved under ignored .local/deployment/.

Run python scripts/smoke_local.py to repeat the stateful local smoke check. It is restricted to localhost/127.0.0.1 and reads the generated local demo credentials. Each run creates demonstration operational records; it does not reset or delete restaurant data.

Generated login details: .local/demo-credentials.json (ignored by Git). Use the admin account for configuration, manager for operations, and customer for ordering/reservations.
