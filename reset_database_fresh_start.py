"""
Complete Database Reset Script
WARNING: This will DELETE ALL DATA including users, files, and media!
Only use in testing/development environments.
"""
import os
import django
import shutil
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
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
        print("❌ Reset cancelled.")
        return
    
    print("\n🔄 Starting complete reset...\n")
    
    # Step 1: Delete database file (SQLite)
    db_path = settings.DATABASES['default']['NAME']
    if os.path.exists(db_path):
        print(f"🗑️  Deleting database: {db_path}")
        os.remove(db_path)
        print("✅ Database deleted")
    
    # Step 2: Delete media files
    media_root = settings.MEDIA_ROOT
    if os.path.exists(media_root):
        print(f"\n🗑️  Deleting media files: {media_root}")
        shutil.rmtree(media_root)
        os.makedirs(media_root)
        print("✅ Media files deleted")
    
    # Step 3: Delete all migration files (except __init__.py)
    print("\n🗑️  Deleting migration files...")
    apps_to_clean = ['accounts', 'admin_app', 'user_app', 'document_tracking', 'notifications']
    
    for app in apps_to_clean:
        migrations_dir = Path(app) / 'migrations'
        if migrations_dir.exists():
            for file in migrations_dir.glob('*.py'):
                if file.name != '__init__.py':
                    file.unlink()
                    print(f"   Deleted: {file}")
    
    print("✅ Migration files deleted")
    
    # Step 4: Create fresh migrations
    print("\n📝 Creating fresh migrations...")
    call_command('makemigrations')
    print("✅ Fresh migrations created")
    
    # Step 5: Run migrations
    print("\n🔄 Running migrations...")
    call_command('migrate')
    print("✅ Migrations applied")
    
    # Step 6: Create superuser
    print("\n👤 Creating superuser...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        print("✅ Superuser created")
        print("   Username: admin")
        print("   Password: admin123")
    
    print("\n" + "=" * 80)
    print("✅ RESET COMPLETE - Fresh database ready!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python manage.py runserver")
    print("2. Login with: admin / admin123")
    print("3. Start testing the new Workforces Department structure")
    print()

if __name__ == '__main__':
    reset_database()
