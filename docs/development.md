# Development

Use Python 3.12 or newer supported by Django 5.2. Create a virtual environment and install requirements-dev.txt. Default manage.py settings load config.development through config.settings. Environment files are read by python-dotenv and never committed. CLI process environment takes precedence.

For PostgreSQL development, set DATABASE_URL and run migrate. The dedicated test settings create a separate test database; the test user needs CREATE DATABASE permission. The first menu search-index migration creates pg_trgm. Managed databases may require an administrator to enable this extension beforehand.

Local Docker: run scripts/initialize_local.py, docker compose up -d --build, then docker compose exec web python manage.py seed_demo. Open the URL in README. Credentials are generated into .local/demo-credentials.json. Configuration is in .env. No secret is embedded in the image. Rerunning seed_demo preserves stock and passwords.

Create an administrator without demo data using python manage.py createsuperuser, then set the restaurant role to ADMIN in the admin panel if desired. Superusers are treated as administrators regardless of role. Configure restaurants, branches, operating hours, categories, menu items, modifiers, tables, ingredients, inventory records and recipes through admin. Assign staff/managers to their branches before using operations screens.

Run Ruff before committing. Install repository hooks using python -m pre_commit install. Migrations ship with model changes. Use service functions for order, reservation, stock and payment mutations. Do not bypass transaction boundaries by updating statuses or stock balances directly. Django admin keeps ledgers read-only.

The frontend uses Django templates and small JavaScript modules, same-origin session cookies and CSRF. No frontend build tool or third-party font request is required. Static files are collected during image build; uploaded images use a separate persistent volume.
