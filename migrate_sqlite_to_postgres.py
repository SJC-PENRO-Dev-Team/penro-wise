"""
Migrate selected user accounts from SQLite to PostgreSQL.

This script:
1. Exports only accounts.User rows with login_role of admin/user from SQLite
2. Clears nullable foreign keys that would require related models
3. Imports only the User model dataset into PostgreSQL using DATABASE_URL from the env

Usage:
    python migrate_sqlite_to_postgres.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


ALLOWED_LOGIN_ROLES = ["admin", "user"]


def print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


def run_manage_py(args: list[str], env: dict[str, str]) -> None:
    subprocess.run([sys.executable, "manage.py", *args], env=env, check=True)


load_dotenv()
postgres_url = os.getenv("DATABASE_URL", "").strip()
export_dir = Path(tempfile.gettempdir())
EXPORT_PATH = export_dir / "wise_penro_sqlite_user_export.json"

print_header("SQLITE TO POSTGRESQL USER MIGRATION")

print("\n1. Exporting eligible users from SQLite...")
print("-" * 70)

# Force SQLite mode before Django loads.
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")

import django

django.setup()

from django.core import serializers
from accounts.models import User

try:
    users = User.objects.filter(login_role__in=ALLOWED_LOGIN_ROLES).order_by("id")
    serialized_users = serializers.serialize(
        "json",
        users,
        indent=2,
        use_natural_foreign_keys=True,
        use_natural_primary_keys=True,
    )
    data = json.loads(serialized_users)
    for item in data:
        item["fields"]["department"] = None

    EXPORT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    admin_count = sum(1 for item in data if item["fields"].get("login_role") == "admin")
    user_count = sum(1 for item in data if item["fields"].get("login_role") == "user")

    print(f"Exported {len(data)} user records to {EXPORT_PATH}")
    print(f"Admin users: {admin_count}")
    print(f"Regular users: {user_count}")
except Exception as error:
    print(f"Export failed: {error}")
    sys.exit(1)

print("\n" + "=" * 70)
print("2. Importing eligible users into PostgreSQL...")
print("-" * 70)

if not postgres_url:
    print("DATABASE_URL is not set in the environment.")
    print("Set DATABASE_URL in .env before importing into PostgreSQL.")
    sys.exit(1)

postgres_host = urlparse(postgres_url).hostname or ""
if postgres_host and "." not in postgres_host and postgres_host not in {"localhost", "127.0.0.1"}:
    print("DATABASE_URL appears to use an internal-only hostname.")
    print("Use the external PostgreSQL URL when running this migration from your local machine.")
    sys.exit(1)

postgres_env = os.environ.copy()
postgres_env["DATABASE_URL"] = postgres_url

try:
    print("\nRunning migrations on PostgreSQL...")
    run_manage_py(["migrate", "--no-input"], postgres_env)
    print("Migrations complete")

    print("\nImporting users...")
    run_manage_py(["loaddata", str(EXPORT_PATH)], postgres_env)
    print("Eligible users imported successfully")

    print("\n" + "=" * 70)
    print("3. Verifying migrated users in PostgreSQL...")
    print("-" * 70)
    run_manage_py(
        [
            "shell",
            "-c",
            (
                "from accounts.models import User; "
                "print('Users migrated:', User.objects.filter(login_role__in=['admin','user']).count()); "
                "print('Admin users:', User.objects.filter(login_role='admin').count()); "
                "print('Regular users:', User.objects.filter(login_role='user').count()); "
                "print('Users with department set:', User.objects.exclude(department__isnull=True).count())"
            ),
        ],
        postgres_env,
    )

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print("\nOnly eligible user accounts were migrated from SQLite to PostgreSQL.")
except subprocess.CalledProcessError as error:
    print(f"Import failed with exit code {error.returncode}")
    print("\nTroubleshooting:")
    print("- Check DATABASE_URL in your environment")
    print("- Ensure the PostgreSQL database is reachable")
    print("- Ensure the target database is ready for loaddata")
    sys.exit(error.returncode or 1)
finally:
    if EXPORT_PATH.exists():
        print(f"\nBackup file saved: {EXPORT_PATH}")
