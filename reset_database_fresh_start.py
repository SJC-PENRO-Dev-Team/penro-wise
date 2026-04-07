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
    """Complete database and media reset."""

    print("=" * 80)
    print("DATABASE & MEDIA RESET - TESTING ENVIRONMENT")
    print("=" * 80)
    print("\nWARNING: This will DELETE:")
    print("  - All database data (users, files, folders, etc.)")
    print("  - All uploaded media files")
    print("  - All migration history")
    print("\n" + "=" * 80)

    response = input("\nType 'YES DELETE EVERYTHING' to confirm: ")
    if response != "YES DELETE EVERYTHING":
        print("Reset cancelled.")
        return

    print("\nStarting complete reset...\n")

    db_path = settings.DATABASES["default"]["NAME"]
    if os.path.exists(db_path):
        print(f"Deleting database: {db_path}")
        os.remove(db_path)
        print("Database deleted")

    media_root = getattr(settings, "MEDIA_ROOT", None)
    if media_root and os.path.exists(media_root):
        print(f"\nDeleting media files: {media_root}")
        shutil.rmtree(media_root)
        os.makedirs(media_root)
        print("Media files deleted")

    print("\nDeleting migration files...")
    apps_to_clean = ["accounts", "admin_app", "user_app", "document_tracking", "notifications"]

    for app in apps_to_clean:
        migrations_dir = Path(app) / "migrations"
        if migrations_dir.exists():
            for file in migrations_dir.glob("*.py"):
                if file.name != "__init__.py":
                    file.unlink()
                    print(f"   Deleted: {file}")

    print("Migration files deleted")

    print("\nCreating fresh migrations...")
    call_command("makemigrations")
    print("Fresh migrations created")

    print("\nRunning migrations...")
    call_command("migrate")
    print("Migrations applied")

    admin_username = os.getenv("RESET_ADMIN_USERNAME", "admin")
    admin_email = os.getenv("RESET_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("RESET_ADMIN_PASSWORD", "")

    if admin_password:
        print("\nCreating superuser from env configuration...")
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
            print("Superuser created")
            print(f"   Username: {admin_username}")
            print(f"   Email: {admin_email}")
    else:
        print("\nSkipping superuser creation because RESET_ADMIN_PASSWORD is not set.")

    print("\n" + "=" * 80)
    print("RESET COMPLETE - Fresh database ready!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    if admin_password:
        print(f"2. Login with: {admin_username} / [password from RESET_ADMIN_PASSWORD]")
    else:
        print("2. Create a superuser manually or set RESET_ADMIN_PASSWORD before running again")


if __name__ == "__main__":
    reset_database()
