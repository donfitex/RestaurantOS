# Database

Production requires PostgreSQL via DATABASE_URL. Start a dedicated local instance using `docker compose -f compose.database.yml up -d` with POSTGRES_PASSWORD set. Put the matching postgresql URL in your ignored .env file. Do not point automated tests at a production database.

Run `python manage.py migrate` for application upgrades. Migration files are committed alongside domain changes. Run `python manage.py makemigrations --check --dry-run` in CI. Use config.testing_postgres for row-lock concurrency tests. SQLite is only a lightweight development/test option and cannot validate PostgreSQL locking behavior.

Use PostgreSQL pg_dump custom-format backups with encryption and retention appropriate for the business. Restore to an isolated database using pg_restore and verify row counts, health, and critical workflows before a recovery cutover. Back up media separately. Never run automatic schema migration from every Gunicorn worker.
