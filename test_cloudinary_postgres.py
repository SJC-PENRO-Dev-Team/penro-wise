"""
Test script to verify PostgreSQL and Cloudinary configuration.
"""

import os

from dotenv import load_dotenv

load_dotenv()

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")
django.setup()

from django.conf import settings
from django.db import connection
import cloudinary.api


print("\n" + "=" * 60)
print("CONFIGURATION TEST")
print("=" * 60)

print("\n1. DATABASE CONFIGURATION")
print("-" * 60)
db_config = settings.DATABASES["default"]
print(f"Engine: {db_config['ENGINE']}")
print(f"Name: {db_config['NAME']}")
print(f"Host: {db_config.get('HOST', 'N/A')}")
print(f"Port: {db_config.get('PORT', 'N/A')}")

with connection.cursor() as cursor:
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print("Database connected successfully")
    print(f"PostgreSQL version: {version[:50]}...")

print("\n2. CLOUDINARY CONFIGURATION")
print("-" * 60)
cloudinary_storage = getattr(settings, "CLOUDINARY_STORAGE", {})
print(f"Cloudinary enabled: {getattr(settings, 'CLOUDINARY_ENABLED', False)}")
print(f"Cloud name: {cloudinary_storage.get('CLOUD_NAME', 'N/A')}")
print(f"API key configured: {'YES' if cloudinary_storage.get('API_KEY') else 'NO'}")
print(f"API secret configured: {'YES' if cloudinary_storage.get('API_SECRET') else 'NO'}")
print(f"Storage backend: {settings.DEFAULT_FILE_STORAGE}")

if getattr(settings, "CLOUDINARY_ENABLED", False):
    result = cloudinary.api.ping()
    print(f"Cloudinary status: {result.get('status', 'OK')}")
