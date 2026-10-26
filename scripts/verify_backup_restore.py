"""Non-destructive backup/restore drill against the local Compose database."""

import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
TABLES = [
    "users_user",
    "restaurants_restaurant",
    "restaurants_branch",
    "menu_menuitem",
    "tables_table",
    "orders_order",
    "orders_orderitem",
    "reservations_reservation",
    "inventory_inventoryitem",
    "inventory_stockmovement",
    "payments_payment",
    "common_auditevent",
]


def run(*arguments):
    return subprocess.run(
        ["docker", "compose", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main():
    values = dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )
    user = os.getenv("POSTGRES_USER", values.get("POSTGRES_USER", "restaurant"))
    database = os.getenv("POSTGRES_DB", values.get("POSTGRES_DB", "restaurant"))
    suffix = uuid4().hex[:10]
    restored_database = "restaurantos_restore_audit_" + suffix
    container_path = f"/tmp/restaurantos-audit-{suffix}.dump"
    destination = ROOT / ".local/backups"
    destination.mkdir(parents=True, exist_ok=True)
    backup_path = destination / f"restaurantos-audit-{suffix}.dump"
    sql = (
        " UNION ALL ".join(
            f"SELECT '{table}', count(*), COALESCE(md5(string_agg(row_to_json(t)::text, '' ORDER BY t.id)), '') FROM {table} t"
            for table in TABLES
        )
        + " ORDER BY 1"
    )

    def snapshot(name):
        output = run(
            "exec",
            "-T",
            "db",
            "psql",
            "--username",
            user,
            "--dbname",
            name,
            "--no-password",
            "--tuples-only",
            "--no-align",
            "--field-separator",
            ",",
            "--command",
            sql,
        )
        rows = {}
        for line in output.splitlines():
            table, count, fingerprint = line.split(",")
            rows[table] = {"count": int(count), "fingerprint": fingerprint}
        return rows

    before = snapshot(database)
    run(
        "exec",
        "-T",
        "db",
        "pg_dump",
        "--username",
        user,
        "--dbname",
        database,
        "--no-password",
        "--format=custom",
        "--file",
        container_path,
    )
    run("cp", f"db:{container_path}", str(backup_path))
    run("exec", "-T", "db", "createdb", "--username", user, "--no-password", restored_database)
    run(
        "exec",
        "-T",
        "db",
        "pg_restore",
        "--username",
        user,
        "--dbname",
        restored_database,
        "--no-password",
        "--no-owner",
        container_path,
    )
    restored = snapshot(restored_database)
    after = snapshot(database)
    if before != after:
        raise RuntimeError(
            "Source data changed during the drill; repeat while local activity is idle."
        )
    if restored != before:
        raise RuntimeError("Restored row counts or fingerprints differ from the source.")
    report = {
        "result": "passed",
        "backup_file": str(backup_path.relative_to(ROOT)),
        "restored_database": restored_database,
        "tables_verified": len(TABLES),
        "rows": {table: row["count"] for table, row in restored.items()},
        "fingerprints_match": True,
        "source_unchanged": True,
    }
    output = ROOT / ".local/deployment/backup-restore.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
