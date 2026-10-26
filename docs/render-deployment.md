# Deploy RestaurantOS on Render

The root `render.yaml` Blueprint defines the production web service, PostgreSQL database, notification worker, and persistent media disk in Frankfurt. It uses the smallest paid plans because Render's free web services sleep, free databases expire after 30 days, free services cannot attach persistent disks, and background workers are paid-only.

## Blueprint resources

- `restaurantos-web`: Docker web service, one 512 MB instance, `/health/` readiness check, and a pre-deploy database migration.
- `restaurantos-db`: PostgreSQL 17, private-network-only access, 1 GB initial storage with autoscaling.
- `restaurantos-notifications`: one 512 MB worker using the transactional notification outbox.
- `restaurantos-media`: 1 GB persistent disk mounted at `/app/media` for validated menu images.

Uploaded media requires a persistent disk, which limits the web service to one instance and causes a short interruption during deploys. Keep the database and web service in Frankfurt to use Render's private network. The Render Postgres connection string is passed to each app service without exposing it in the repository.

## Create and deploy

1. Confirm the estimates on Render's pricing page before applying the Blueprint. The minimum baseline is about **$20.55 USD/month**, before bandwidth above the Hobby workspace's included amount and any storage autoscaling: web $7, worker $7, PostgreSQL compute $6, 1 GB database storage $0.30, and 1 GB media disk $0.25.
2. Open the Render Dashboard, choose **New > Blueprint**, and connect `donfitex/RestaurantOS` on `main`.
3. Review the three paid resources and the persistent disk. Do not select free compute for production data.
4. Enter the SMTP host, SMTP username/password, and verified sender address when prompted. Use the provider's STARTTLS SMTP endpoint on port 587. Do not commit these values.
5. Apply the Blueprint and monitor the web and worker deploys. Database migrations run in the web service's pre-deploy step.
6. Confirm `/health/` returns `200` with both database and notification-worker checks healthy.
7. Create the first production administrator from a Render one-off shell or shell session with `python manage.py createsuperuser`. Do not copy the local demo accounts or demo password into production.
8. Configure the live restaurant, branches, menu, tables, staff, and business hours in Django admin before opening ordering to customers.

Render supplies the `onrender.com` URL and TLS automatically. `config.production` adds Render's assigned hostname and HTTPS origin at runtime. The application trusts `X-Forwarded-For` only when Render's documented `RENDER=true` marker is present, so database-backed rate limits remain separated by client address behind Render's proxy.

## Production follow-up

- Verify SMTP delivery through both the web process (password resets) and notification worker (outbox events).
- Set up an external monitoring target for `/health/`, inspect failed outbox records, and regularly export a database backup outside Render.
- Add a custom domain only after its owner and DNS records are available. Use the domain in `CSRF_TRUSTED_ORIGINS` if it differs from the assigned Render hostname.
- Payment records are staff-verified ledger entries; this release does not connect a live payment processor.
