# RestaurantOS

A modular Django platform for restaurant and branch operations: menus, ordering, kitchen workflow, reservations, table management, recipes, inventory, payments, reporting, and staff permissions.

## Start locally with Docker

Requirements: Docker Desktop/Engine and Python for the local setup script.

```powershell
python scripts/initialize_local.py
docker compose up -d --build
docker compose exec web python manage.py seed_demo
```

Open http://127.0.0.1:8000. Generated local demo credentials are in `.local/demo-credentials.json`, which is ignored by Git. The setup script preserves existing environment values. Demo accounts include administrator, manager, waiter, cashier, kitchen, inventory manager, and customer. The demo seed is idempotent and does not reset existing passwords or stock. Never deploy demo accounts publicly.

The local deployment uses PostgreSQL, Gunicorn, a notification worker, and persistent database/media volumes. It binds only to loopback. Local HTTP mode uses DEBUG=False but relaxes HTTPS-only cookies for local browsing. Public deployment must use config.production with HTTPS and real secrets.

Useful pages: `/menu/`, `/reservations/`, `/cart/`, `/my/`, `/staff/`, `/admin/`, `/api/docs/`, `/health/`.

## Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Default development uses SQLite; PostgreSQL is required for production and concurrency verification. See [development](docs/development.md) and [database](docs/database.md).

## Verification

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest -m "not e2e"
python -m playwright install chromium
python -m pytest -m e2e
```

Run PostgreSQL tests with `DJANGO_SETTINGS_MODULE=config.testing_postgres` and a dedicated DATABASE_URL. CI runs PostgreSQL tests on Python 3.12/3.13, real browser workflows, schema validation, security checks, coverage, and a container build. [Testing guide](docs/testing.md).

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api.md) and [OpenAPI schema](docs/openapi.yaml)
- [Development](docs/development.md)
- [Testing](docs/testing.md)
- [Security](docs/security.md)
- [Database and recovery](docs/database.md)
- [Deployment](docs/deployment.md)
- [Restaurant operations](docs/restaurant-operations.md)
- [Plan progress](docs/PROGRESS.md)
- [Verified local deployment](docs/local-deployment.md)
- [Release audit](docs/release-audit.md)

Payment records are a staff-verified ledger; a live payment provider is an integration boundary. Local email uses the console backend. Configure SMTP for real notification delivery.
