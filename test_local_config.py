"""
Quick test to verify local development configuration
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.conf import settings

print("\n" + "="*60)
print("LOCAL DEVELOPMENT CONFIGURATION TEST")
print("="*60)

# Test Database
print("\n📊 DATABASE CONFIGURATION:")
db_config = settings.DATABASES['default']
print(f"  Engine: {db_config['ENGINE']}")
if 'sqlite' in db_config['ENGINE'].lower():
    print(f"  ✓ Using SQLite3 (LOCAL MODE)")
    print(f"  Database file: {db_config['NAME']}")
else:
    print(f"  ✓ Using PostgreSQL (PRODUCTION MODE)")
    print(f"  Host: {db_config.get('HOST', 'N/A')}")

# Test File Storage
print("\n📁 FILE STORAGE CONFIGURATION:")
cloudinary_enabled = getattr(settings, 'CLOUDINARY_ENABLED', False)
if cloudinary_enabled:
    print(f"  ✓ Cloudinary enabled (PRODUCTION MODE)")
    print(f"  Cloud name: {settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', 'N/A')}")
else:
    print(f"  ✓ Local file storage enabled (DEVELOPMENT MODE)")
    print(f"  Storage backend: {settings.DEFAULT_FILE_STORAGE}")
    print(f"  Media root: {settings.MEDIA_ROOT}")
    print(f"  Media URL: {settings.MEDIA_URL}")

# Test Debug Mode
print("\n🐛 DEBUG MODE:")
print(f"  DEBUG = {settings.DEBUG}")

# Test Installed Apps
print("\n📦 KEY INSTALLED APPS:")
key_apps = ['accounts', 'admin_app', 'user_app', 'structure', 'notifications']
for app in key_apps:
    if any(app in installed_app for installed_app in settings.INSTALLED_APPS):
        print(f"  ✓ {app}")

print("\n" + "="*60)
print("CONFIGURATION TEST COMPLETE")
print("="*60)

# Check if media directory exists
import pathlib
media_path = pathlib.Path(settings.MEDIA_ROOT)
if not media_path.exists():
    print(f"\n⚠️  Media directory does not exist yet: {media_path}")
    print(f"   It will be created automatically when files are uploaded.")
else:
    print(f"\n✓ Media directory exists: {media_path}")

print("\n✅ Ready for local development!")
print("   Run: python manage.py runserver")
print("\n")
