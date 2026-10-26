# Database

Production requires PostgreSQL via DATABASE_URL. Start a dedicated local instance using `docker compose -f compose.database.yml up -d` with POSTGRES_PASSWORD set. Put the matching postgresql URL in your ignored .env file. Do not point automated tests at a production database.

Run `python manage.py migrate` for application upgrades. Migration files are committed alongside domain changes. Run `python manage.py makemigrations --check --dry-run` in CI. Use config.testing_postgres for row-lock concurrency tests. SQLite is only a lightweight development/test option and cannot validate PostgreSQL locking behavior.

Use PostgreSQL pg_dump custom-format backups with encryption and retention appropriate for the business. Restore to an isolated database using pg_restore and verify row counts, health, and critical workflows before a recovery cutover. Back up media separately. Never run automatic schema migration from every Gunicorn worker.


## Backup and restore drill

Use pg_dump --format=custom against the application database. Within Compose, write the dump inside the database container then copy it to protected backup storage using docker compose cp. Avoid piping binary dumps through Windows PowerShell text redirection. Encrypt backups off-host and retain media snapshots from the same operational period.

Restore to a newly created isolated database using pg_restore --no-owner. Verify migrations, table counts, menu data, health and representative order/reservation operations before switching traffic. A backup is not considered verified until a restore drill succeeds. The release audit records the local drill separately from production backup policy.

The pg_trgm extension powers the menu search index. Provision it through a database administrator if the migration identity cannot create extensions. Use a non-superuser application identity in public production and a separate migration identity for schema work.

Run `python scripts/verify_backup_restore.py` for the repeatable local Compose drill. It creates a new restore database and preserves the live database, compares core-table counts and fingerprints, and saves a report under .local/deployment/. Local dump files and the restored audit database are retained for inspection.
