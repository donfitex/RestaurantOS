# Deployment

The default Compose deployment binds HTTP to 127.0.0.1 only, uses PostgreSQL, and runs Gunicorn with two threaded workers. config.local deliberately disables HTTPS-only cookies and redirects for loopback testing while retaining DEBUG=False and production secret/database validation. Never expose this local mode on a public interface.

Public production must use config.production behind a trusted HTTPS reverse proxy. Set a random SECRET_KEY (50+ characters), explicit ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS with https origins, and a PostgreSQL DATABASE_URL. Do not expose the database port. Run migrations once per release before starting workers. Review schema changes and back up before deployment.

For Render deployment, use the production Blueprint in `render.yaml` and its service, database, SMTP, storage, and initialization runbook in `docs/render-deployment.md`.

Gunicorn configuration lives in gunicorn.conf.py. Tune WEB_CONCURRENCY and GUNICORN_THREADS to database connections and memory. Worker recycling bounds long-lived process growth; graceful timeouts support rolling restarts. Do not trust arbitrary forwarded headers. FORWARDED_ALLOW_IPS must identify only the reverse proxy; configure the proxy to overwrite client-supplied forwarding headers. External TLS termination must also have a deliberate trusted scheme configuration before enabling redirection.

The notification worker runs as a separate process and supports SIGTERM/SIGINT graceful shutdown. Configure SMTP credentials through the environment. The local console backend demonstrates outbox delivery without sending real email. Run cleanup_rate_limits periodically. Monitor the outbox for FAILED messages.

Application code runs as a non-root user. Persistent database and media volumes survive container replacement. Never run `docker compose down -v` unless intentionally deleting local data. Rebuild after code updates. Additional deployment and recovery steps are recorded in the release audit.


## Local runbook

1. Run python scripts/initialize_local.py.
2. Run docker compose up -d --build. The database health check gates a one-shot migration container; web and worker start after migration success.
3. Run docker compose exec web python manage.py seed_demo only for a local demo.
4. Check docker compose ps, GET /health/ and GET /health/live/.
5. Log in with local generated credentials and verify menu, order, stock deduction, reservation, payment, reports and admin access.
6. Stop services using docker compose stop. Restart with docker compose up -d. Do not remove volumes during ordinary updates.

Static files use WhiteNoise manifest storage in production/local mode. Uploaded images persist in media_data. Local mode serves only allowed image extensions through a restricted view. Public production should serve media from a separate origin/object storage with no executable content and the documented image validator; configure media URL, CSP image sources and storage adapter together.

For HTTPS termination, keep Django reachable only from the reverse proxy, overwrite incoming forwarding headers there, configure the trusted scheme setting explicitly, and test secure cookies plus redirects. The local HTTP deployment does not establish public TLS, a domain, external SMTP, managed backups or a payment-provider account.

Before upgrades: export an encrypted database backup and copy media. Run migrations with a dedicated deployment identity, then start the new image and verify health. Keep the prior image and backup until smoke tests pass. Roll back application code only when its schema is compatible; otherwise restore to a separate database and perform a deliberate cutover.
