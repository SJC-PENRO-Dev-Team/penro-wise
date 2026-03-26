#!/usr/bin/env python
"""
Quick script to check which database Django is configured to use
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("DATABASE CONFIGURATION CHECK")
print("=" * 60)

db_config = settings.DATABASES['default']

print(f"\nEngine: {db_config.get('ENGINE', 'Not set')}")
print(f"Name: {db_config.get('NAME', 'Not set')}")
print(f"Host: {db_config.get('HOST', 'Not set')}")
print(f"Port: {db_config.get('PORT', 'Not set')}")
print(f"User: {db_config.get('USER', 'Not set')}")

print("\n" + "=" * 60)

# Check if it's SQLite
if 'sqlite' in db_config.get('ENGINE', '').lower():
    print("✅ Using SQLite3 (Local Database)")
    print(f"   Database file: {db_config.get('NAME')}")
elif 'postgresql' in db_config.get('ENGINE', '').lower():
    print("⚠️  Using PostgreSQL (Remote Database)")
    print(f"   Host: {db_config.get('HOST')}")
    print(f"   Database: {db_config.get('NAME')}")
else:
    print(f"❓ Using: {db_config.get('ENGINE')}")

print("=" * 60)

# Check environment variable
print("\nEnvironment Variables:")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
print(f"DEBUG: {settings.DEBUG}")
print("=" * 60)
