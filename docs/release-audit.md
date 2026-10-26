# Local release audit

Date: 2026-10-26, Africa/Lagos.

Result: local release passed. Application source: df411748910db073f833308299a7fe63e21013cd. The selected deployment target is a local container, as requested. This audit does not claim a public production launch.

## Verification

| Check | Result |
| --- | --- |
| Complete PostgreSQL test suite, including browser workflows | 106 passed |
| Application coverage | 90.04% (85% gate passed) |
| Real PostgreSQL concurrency regressions | Passed |
| Ruff lint and formatting | Passed |
| Migration-state consistency | Passed |
| OpenAPI validation and schema consistency | Passed |
| CI: Python 3.12 and 3.13/PostgreSQL | Passed |
| CI: Linux Chromium workflows | Passed |
| CI: container build | Passed |
| Running Docker application smoke test | Passed |
| Database and notification-worker readiness | Healthy |
| Non-root web process | UID 999 |
| Runtime debug flag | False |
| Production security configuration check | No warnings |
| Persistent media and manifest static storage | Verified |
| Mobile menu horizontal-overflow check | Passed |
| Backup/restore drill | Passed for 12 core tables |

CI evidence for the audited application revision: https://github.com/donfitex/RestaurantOS/actions/runs/40330068813

## Operational verification

The real container deployment verified customer checkout, manager confirmation/preparation/ready/completion, staff payment submission, receipt rendering, recipe-driven stock deduction, restocking, signed adjustments, movement history, reservation creation/confirmation/cancellation, slot release, reports, dashboards, administrator access, API docs and health endpoints.

Release corrections cover cross-branch isolation, customer ownership, discount/refund permissions, invalid transitions, idempotent retries, global reference races, cancellation races, nonnegative inventory, transactional rollback, price snapshots, historical stock restoration, staff audit attribution, stale-alert suppression, kitchen history/scoping, superuser UI access, PostgreSQL locking and case-insensitive search indexes.

## Recovery evidence

A custom-format PostgreSQL dump was copied to ignored local backup storage and restored into a newly created isolated database. Counts and complete row fingerprints matched across 12 core tables. The source data remained unchanged. The restored database is restaurantos_restore_audit_76453acabd; the backup is .local/backups/restaurantos-audit-76453acabd.dump.

Verified core records included 7 users, 6 menu items, 2 orders, 1 payment record, 11 stock movements, 1 reservation and 24 audit events. This is a local restore drill; off-host encrypted retention and a production recovery schedule still require a production environment.

## Current delivery and external prerequisites

The app is running at http://127.0.0.1:8000. Generated local account details are in .local/demo-credentials.json and are excluded from Git. Database and media volumes persist across container replacement.

Public hosting, a production domain/TLS termination, production SMTP credentials and managed backup/monitoring destinations have not been configured. config.production and the deployment runbook are prepared for that environment. The current local HTTP mode deliberately relaxes HTTPS-only cookies while retaining DEBUG=False and the other local security controls.

Payments are a staff-verified ledger, as specified in the master plan; no external charge is made. A live payment provider is a future integration boundary. Local notifications use the console backend. Demo restaurant information and images can be replaced through admin.
