"""
Prepare for Workforces Department Refactor - Migration Cleanup

This script:
1. Backs up current migration files
2. Deletes old migrations (except __init__.py)
3. Prepares for fresh migration creation

Run this BEFORE creating new migrations.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def backup_migrations():
    """Create backup of current migrations."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"migrations_backup_{timestamp}")
    backup_dir.mkdir(exist_ok=True)
    
    print(f"📦 Creating backup in: {backup_dir}")
    
    # Backup accounts migrations
    accounts_backup = backup_dir / "accounts"
    accounts_backup.mkdir(exist_ok=True)
    shutil.copytree(
        "accounts/migrations",
        accounts_backup / "migrations",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    
    # Backup structure migrations
    structure_backup = backup_dir / "structure"
    structure_backup.mkdir(exist_ok=True)
    shutil.copytree(
        "structure/migrations",
        structure_backup / "migrations",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )
    
    print(f"✅ Backup created successfully")
    return backup_dir

def delete_migration_files(app_name):
    """Delete all migration files except __init__.py"""
    migrations_dir = Path(app_name) / "migrations"
    
    if not migrations_dir.exists():
        print(f"⚠️  {migrations_dir} does not exist")
        return
    
    deleted_count = 0
    for file in migrations_dir.glob("*.py"):
        if file.name != "__init__.py":
            print(f"  🗑️  Deleting: {file}")
            file.unlink()
            deleted_count += 1
    
    # Also delete __pycache__
    pycache_dir = migrations_dir / "__pycache__"
    if pycache_dir.exists():
        print(f"  🗑️  Deleting: {pycache_dir}")
        shutil.rmtree(pycache_dir)
    
    print(f"✅ Deleted {deleted_count} migration files from {app_name}")

def main():
    print("=" * 70)
    print("WORKFORCES DEPARTMENT REFACTOR - MIGRATION CLEANUP")
    print("=" * 70)
    print()
    
    # Confirm
    print("⚠️  WARNING: This will delete all existing migration files!")
    print("   A backup will be created first.")
    print()
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("❌ Aborted")
        return
    
    print()
    
    # Step 1: Backup
    backup_dir = backup_migrations()
    print()
    
    # Step 2: Delete migrations
    print("🗑️  Deleting old migrations...")
    delete_migration_files("accounts")
    delete_migration_files("structure")
    print()
    
    # Step 3: Instructions
    print("=" * 70)
    print("✅ MIGRATION CLEANUP COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print()
    print("1. Create fresh migrations:")
    print("   python manage.py makemigrations accounts")
    print("   python manage.py makemigrations structure")
    print()
    print("2. Reset database:")
    print("   python reset_database_fresh_start.py")
    print()
    print("3. Apply migrations:")
    print("   python manage.py migrate")
    print()
    print("4. Create default department:")
    print("   python manage.py shell")
    print("   >>> from accounts.models import WorkforcesDepartment")
    print("   >>> WorkforcesDepartment.objects.create(")
    print("   ...     name='Workforces Department',")
    print("   ...     description='Unified department for all workforce members',")
    print("   ...     is_active=True")
    print("   ... )")
    print()
    print("5. Create superuser:")
    print("   python manage.py createsuperuser")
    print()
    print(f"📦 Backup location: {backup_dir}")
    print()

if __name__ == "__main__":
    main()
