"""
Quick Reset for Workforces Refactor

Deletes database and all migration files to start fresh.
"""

import os
import shutil
from pathlib import Path

def delete_database():
    """Delete the SQLite database."""
    db_path = Path("db.sqlite3")
    if db_path.exists():
        print(f"🗑️  Deleting database: {db_path}")
        db_path.unlink()
        print("✅ Database deleted")
    else:
        print("⚠️  Database not found (already deleted?)")

def delete_migrations(app_name):
    """Delete all migration files except __init__.py"""
    migrations_dir = Path(app_name) / "migrations"
    
    if not migrations_dir.exists():
        print(f"⚠️  {migrations_dir} does not exist")
        return
    
    deleted_count = 0
    for file in migrations_dir.glob("*.py"):
        if file.name != "__init__.py":
            print(f"  🗑️  {file}")
            file.unlink()
            deleted_count += 1
    
    # Delete __pycache__
    pycache_dir = migrations_dir / "__pycache__"
    if pycache_dir.exists():
        print(f"  🗑️  {pycache_dir}")
        shutil.rmtree(pycache_dir)
    
    print(f"✅ Deleted {deleted_count} migration files from {app_name}")

def main():
    print("=" * 70)
    print("QUICK RESET FOR WORKFORCES REFACTOR")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Delete db.sqlite3")
    print("  2. Delete ALL migration files (except __init__.py)")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("❌ Aborted")
        return
    
    print()
    
    # Delete database
    delete_database()
    print()
    
    # Delete migrations from all apps
    apps = [
        "accounts",
        "structure",
        "admin_app",
        "user_app",
        "notifications",
        "document_tracking",
    ]
    
    print("🗑️  Deleting migrations...")
    for app in apps:
        delete_migrations(app)
    print()
    
    print("=" * 70)
    print("✅ RESET COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. Create fresh migrations:")
    print("   python manage.py makemigrations")
    print()
    print("2. Apply migrations:")
    print("   python manage.py migrate")
    print()
    print("3. Create default department:")
    print("   python create_default_department.py")
    print()
    print("4. Create superuser:")
    print("   python manage.py createsuperuser")
    print()

if __name__ == "__main__":
    main()
