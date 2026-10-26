# Security

Production validates SECRET_KEY, explicit ALLOWED_HOSTS, and a PostgreSQL URL. Keep .env and credentials out of Git. HTTPS redirection, secure cookies, HSTS, CSRF, clickjacking protection, same-origin CSP and permission headers are enabled. Serve uploaded media from an isolated media host in public production (see storage guidance).

Session authentication requires CSRF on unsafe methods. Registration cannot select roles. Administrators provision staff and branch membership. Staff APIs scope records to assigned or managed branches; customer APIs scope ownership. Django admin is restricted to administrators with is_staff set. Ledgers are immutable through admin. Discounts, refunds, kitchen transitions and stock writes have specific role checks.

Database-backed rate buckets share limits across application workers: anonymous 60/minute, authenticated 600/minute, authentication submissions 10/minute per direct source address. Forwarded IP headers are deliberately not trusted. Configure the reverse proxy to supply a trustworthy remote address before exposing a shared proxy to many users. Run cleanup_rate_limits periodically. Same-origin access is the default; no permissive CORS configuration is enabled.

Payment APIs record staff-verified transactions. No customer may self-settle a payment. Integrate a provider by verifying signatures, amount, currency and reference before calling ledger services. Full payment is required to complete an order; recorded funds must be refunded before cancellation. This application does not collect card details.

Notification delivery is at least once; SMTP timeouts after acceptance can duplicate a message. Monitor FAILED outbox records and retry only after addressing the cause. Logs omit secrets and email bodies. Backups and deployment credentials require least privilege and rotation.
