# Deploy RestaurantOS on Render Free with Neon

The root `render.yaml` Blueprint creates one free Render Docker web service and uses the external Neon PostgreSQL database supplied through `DATABASE_URL`. It does not create a Render database, background worker, or persistent disk.

## Configure Neon

The Django application already uses `dj-database-url` and `psycopg` to connect to PostgreSQL. Use the pooled Neon `DATABASE_URL` for web traffic and the direct `DATABASE_URL_UNPOOLED` for schema migrations. Keep both in ignored environment files or a secret manager; never commit either connection string. The Render startup command temporarily selects the direct URL for migrations, then Gunicorn uses the pooled URL.

```powershell
npm.cmd install --global neon@latest
neon.cmd login
neon.cmd init -y --org-id org-steep-field-51623490 --project-id plain-dew-42324195 --branch production --services postgres --agent codex
neon.cmd deploy
```

The Neon CLI's project setup also configures its Codex integration. If browser sign-in is requested, complete it in the browser before rerunning `neon init`. The CLI should pull `DATABASE_URL` into the existing ignored `.env` file.

## Apply the Render Blueprint

1. Open the Render Dashboard and create a Blueprint from `donfitex/RestaurantOS` on `main`.
2. Select the Free plan and provide both Neon connection strings when prompted: pooled `DATABASE_URL` and direct `DATABASE_URL_UNPOOLED`. Do not include either URL in source control or a public issue.
3. Apply the Blueprint and wait for the Docker build and deploy. The startup command runs Django migrations before Gunicorn starts.
4. Check `/health/`. Free Render services do not provide an interactive shell, so create the first administrator from a local checkout after Neon has deployed the schema: run `python manage.py migrate` with `DATABASE_URL_UNPOOLED` as `DATABASE_URL`, then run `python manage.py createsuperuser` with the pooled `DATABASE_URL`. Configure the restaurant and its real data in the admin site.

Render supplies the `onrender.com` hostname and TLS. `config.production` adds the assigned hostname and HTTPS origin at runtime.

## Free-plan limitations

- Render's free web service sleeps after inactivity and has an ephemeral filesystem. Requests can be slow after idle periods, and locally stored uploaded menu images can disappear after a restart or redeploy.
- Render does not provide a free background worker. The notification worker is omitted and `REQUIRE_NOTIFICATION_WORKER` is disabled, so queued notification outbox messages will not be processed automatically.
- The default Django email backend writes messages to application logs; it does not deliver password resets or notifications to inboxes.
- Neon and Render free plans have usage and availability limits. This setup is suited to a demo or evaluation, not a production restaurant relying on continuous availability, durable media, or automatic notifications.

To move beyond a demo, add durable object storage for media, an always-on notification worker and SMTP provider, and monitor database usage and backups.

Payment records remain staff-verified ledger entries; this release does not connect a live payment processor.
