"""
Migrate selected user accounts from SQLite to PostgreSQL.

This script:
1. Exports only accounts.User rows with login_role of admin/user from SQLite
2. Clears nullable foreign keys that would require related models
3. Imports only the User model dataset into PostgreSQL using DATABASE_URL from the env
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


def run_manage_py(args: list[str], env: dict[str, str]) -> None:
    subprocess.run([sys.executable, "manage.py", *args], env=env, check=True)


load_dotenv()
postgres_url = os.getenv("DATABASE_URL", "").strip()
EXPORT_PATH = Path(tempfile.gettempdir()) / "wise_penro_sqlite_user_export.json"

os.environ["DATABASE_URL"] = ""
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")

import django

django.setup()

from django.core import serializers
from accounts.models import User

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
print(f"Exported {len(data)} user records to {EXPORT_PATH}")

if not postgres_url:
    print("DATABASE_URL is not set in the environment.")
    raise SystemExit(1)

postgres_host = urlparse(postgres_url).hostname or ""
if postgres_host and "." not in postgres_host and postgres_host not in {"localhost", "127.0.0.1"}:
    print("DATABASE_URL appears to use an internal-only hostname.")
    raise SystemExit(1)

postgres_env = os.environ.copy()
postgres_env["DATABASE_URL"] = postgres_url
run_manage_py(["migrate", "--no-input"], postgres_env)
run_manage_py(["loaddata", str(EXPORT_PATH)], postgres_env)
