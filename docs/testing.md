# Testing

Install requirements-dev.txt. Run `python -m pytest` for the SQLite suite. Run `python -m pytest --cov=apps --cov-report=term-missing` to review coverage. Domain regression tests ship with their implementation; later tests exercise cross-domain behavior.

PostgreSQL-only concurrency tests are marked postgres and skip explicitly on SQLite. Run with `DJANGO_SETTINGS_MODULE=config.testing_postgres` and a dedicated DATABASE_URL whose user may create test databases. Never reuse production credentials. CI provisions an isolated PostgreSQL service.

Factories produce related data from one restaurant consistently. Tests must use transaction boundaries for constraint failures. Transaction tests use separate connections and synchronize competing workers.
