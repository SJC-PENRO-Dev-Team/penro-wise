"""
Quick test to verify local development configuration.
"""

import os
import pathlib

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")
django.setup()

from django.conf import settings


print("\n" + "=" * 60)
print("LOCAL DEVELOPMENT CONFIGURATION TEST")
print("=" * 60)

db_config = settings.DATABASES["default"]
print("\nDATABASE CONFIGURATION:")
print(f"  Engine: {db_config['ENGINE']}")
print(f"  Database: {db_config['NAME']}")

print("\nFILE STORAGE CONFIGURATION:")
cloudinary_enabled = getattr(settings, "CLOUDINARY_ENABLED", False)
print(f"  Cloudinary enabled: {cloudinary_enabled}")
print(f"  Cloud name: {getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'N/A')}")
print(f"  Storage backend: {settings.DEFAULT_FILE_STORAGE}")
print(f"  Media root: {getattr(settings, 'MEDIA_ROOT', 'N/A')}")

media_root = getattr(settings, "MEDIA_ROOT", None)
if media_root:
    media_path = pathlib.Path(media_root)
    print(f"\nMedia path exists: {media_path.exists()}")
