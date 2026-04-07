"""
Complete Database Reset Script
WARNING: This will DELETE ALL DATA including users, files, and media!
Only use in testing/development environments.
"""

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")
django.setup()

from django.conf import settings
from django.core.management import call_command


def reset_database():
    db_path = settings.DATABASES["default"]["NAME"]
    if os.path.exists(db_path):
        os.remove(db_path)

    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_root and os.path.exists(media_root):
        shutil.rmtree(media_root)
        os.makedirs(media_root)

    apps_to_clean = ["accounts", "admin_app", "user_app", "document_tracking", "notifications"]
    for app in apps_to_clean:
        migrations_dir = Path(app) / "migrations"
        if migrations_dir.exists():
            for file in migrations_dir.glob("*.py"):
                if file.name != "__init__.py":
                    file.unlink()

    call_command("makemigrations")
    call_command("migrate")

    admin_username = os.getenv("RESET_ADMIN_USERNAME", "admin")
    admin_email = os.getenv("RESET_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("RESET_ADMIN_PASSWORD", "")

    if admin_password:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name="Admin",
                last_name="User",
            )


if __name__ == "__main__":
    reset_database()
