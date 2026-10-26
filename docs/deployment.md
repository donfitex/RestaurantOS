# Deployment

The default Compose deployment binds HTTP to 127.0.0.1 only, uses PostgreSQL, and runs Gunicorn with two threaded workers. config.local deliberately disables HTTPS-only cookies and redirects for loopback testing while retaining DEBUG=False and production secret/database validation. Never expose this local mode on a public interface.

Public production must use config.production behind a trusted HTTPS reverse proxy. Set a random SECRET_KEY (50+ characters), explicit ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS with https origins, and a PostgreSQL DATABASE_URL. Do not expose the database port. Run migrations once per release before starting workers. Review schema changes and back up before deployment.

Gunicorn configuration lives in gunicorn.conf.py. Tune WEB_CONCURRENCY and GUNICORN_THREADS to database connections and memory. Worker recycling bounds long-lived process growth; graceful timeouts support rolling restarts. Do not trust arbitrary forwarded headers. FORWARDED_ALLOW_IPS must identify only the reverse proxy; configure the proxy to overwrite client-supplied forwarding headers. External TLS termination must also have a deliberate trusted scheme configuration before enabling redirection.

The notification worker runs as a separate process and supports SIGTERM/SIGINT graceful shutdown. Configure SMTP credentials through the environment. The local console backend demonstrates outbox delivery without sending real email. Run cleanup_rate_limits periodically. Monitor the outbox for FAILED messages.

Application code runs as a non-root user. Persistent database and media volumes survive container replacement. Never run `docker compose down -v` unless intentionally deleting local data. Rebuild after code updates. Additional deployment and recovery steps are recorded in the release audit.
