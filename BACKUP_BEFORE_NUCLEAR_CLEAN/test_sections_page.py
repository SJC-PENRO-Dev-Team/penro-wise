"""
Test script to verify sections page is working correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Section
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("SECTIONS PAGE TEST")
print("=" * 60)

# Check if migration was applied
print("\n1. Checking Section model fields...")
section_fields = [f.name for f in Section._meta.get_fields()]
required_fields = ['display_name', 'description', 'is_active', 'order', 'updated_at']

for field in required_fields:
    if field in section_fields:
        print(f"   ✓ {field} exists")
    else:
        print(f"   ✗ {field} MISSING")

# Check existing sections
print("\n2. Checking existing sections...")
sections = Section.objects.all()
print(f"   Total sections: {sections.count()}")

for section in sections:
    print(f"\n   Section: {section.name}")
    print(f"   - Display Name: {section.display_name}")
    print(f"   - Description: {section.description or '(none)'}")
    print(f"   - Active: {section.is_active}")
    print(f"   - Order: {section.order}")

# Check admin users
print("\n3. Checking admin users...")
admins = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)
print(f"   Total admin users: {admins.count()}")
for admin in admins:
    print(f"   - {admin.username} (staff={admin.is_staff}, super={admin.is_superuser})")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Visit: http://127.0.0.1:8000/documents/admin/settings/sections/")
print("2. Run: python manage.py create_default_sections")
print("3. Test department assignment on submission detail page")
