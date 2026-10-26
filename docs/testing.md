# Testing

Install requirements-dev.txt. Run `python -m pytest` for the SQLite suite. Run `python -m pytest --cov=apps --cov-report=term-missing` to review coverage. Domain regression tests ship with their implementation; later tests exercise cross-domain behavior.

PostgreSQL-only concurrency tests are marked postgres and skip explicitly on SQLite. Run with `DJANGO_SETTINGS_MODULE=config.testing_postgres` and a dedicated DATABASE_URL whose user may create test databases. Never reuse production credentials. CI provisions an isolated PostgreSQL service.

Factories produce related data from one restaurant consistently. Tests must use transaction boundaries for constraint failures. Transaction tests use separate connections and synchronize competing workers.

Browser CI uses PostgreSQL as well: concurrent browser requests must not share the SQLite in-memory live-server connection. Local browser runs should use config.testing_postgres for the same production-like behavior. The checked-in OpenAPI schema is generated with PostgreSQL settings because model integer bounds depend on the database backend.

CI pins Ubuntu 24.04 and uses its installed Google Chrome through Playwright's chrome channel, avoiding an extra browser/dependency download. The job checks the installed browser version before running the full UI workflows. References: https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md and https://playwright.dev/python/docs/browsers.
