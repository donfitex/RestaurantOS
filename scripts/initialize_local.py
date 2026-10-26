"""Create missing local configuration without overwriting existing values."""

import json
import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    existing = env_file.read_text() if env_file.exists() else ""
    values = dict(
        line.split("=", 1)
        for line in existing.splitlines()
        if "=" in line and not line.startswith("#")
    )
    defaults = {
        "SECRET_KEY": secrets.token_urlsafe(64),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "ALLOWED_HOSTS": "localhost,127.0.0.1",
        "APP_PORT": "8000",
        "DEMO_PASSWORD": secrets.token_urlsafe(24),
    }
    additions = {key: value for key, value in defaults.items() if key not in values}
    if additions:
        with env_file.open("a") as stream:
            stream.write(
                "\n" + "\n".join(f"{key}={value}" for key, value in additions.items()) + "\n"
            )
    values.update(additions)
    local = root / ".local"
    local.mkdir(exist_ok=True)
    credentials = {
        "url": f"http://127.0.0.1:{values['APP_PORT']}",
        "accounts": ["admin", "manager", "waiter", "cashier", "kitchen", "inventory", "customer"],
        "password": values["DEMO_PASSWORD"],
        "purpose": "Local demonstration only. Never use these demo accounts in public production.",
    }
    (local / "demo-credentials.json").write_text(json.dumps(credentials, indent=2) + "\n")
    print(
        "Local configuration initialized. Demo credentials are in .local/demo-credentials.json (ignored by Git)."
    )


if __name__ == "__main__":
    main()
