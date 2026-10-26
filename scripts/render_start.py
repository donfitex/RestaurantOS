"""Run Neon migrations over the direct connection, then serve with Gunicorn."""

import os
import subprocess
import sys


def main():
    direct_url = os.environ.get("DATABASE_URL_UNPOOLED")
    if not direct_url:
        raise RuntimeError("DATABASE_URL_UNPOOLED is required for Render migrations")

    migration_environment = os.environ.copy()
    migration_environment["DATABASE_URL"] = direct_url
    print("Applying Django migrations using the direct database connection", flush=True)
    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        check=True,
        env=migration_environment,
    )

    print("Starting Gunicorn using the pooled application connection", flush=True)
    os.execvpe(
        "gunicorn",
        ["gunicorn", "config.wsgi:application", "--config", "gunicorn.conf.py"],
        os.environ.copy(),
    )


if __name__ == "__main__":
    main()
