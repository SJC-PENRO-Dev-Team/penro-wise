#!/usr/bin/env python
"""Move Submissions category to correct location"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder

print("=" * 60)
print("MOVING SUBMISSIONS TO CORRECT LOCATION")
print("=" * 60)

# Get the main ROOT and its 2026 year folder
main_root = DocumentFolder.objects.get(id=10, name="ROOT")
year_2026 = DocumentFolder.objects.get(id=11, parent=main_root, folder_type='year')

print(f"\nMain ROOT: {main_root.name} (ID: {main_root.id})")
print(f"Year folder: {year_2026.name} (ID: {year_2026.id})")

# Get the Submissions category (currently under Document Tracking ROOT)
submissions_category = DocumentFolder.objects.get(id=85, name="Submissions", folder_type='category')

print(f"\nSubmissions category: {submissions_category.name} (ID: {submissions_category.id})")
print(f"Current parent: {submissions_category.parent.name} (ID: {submissions_category.parent.id})")

# Move Submissions to be under the main 2026 folder
print(f"\nMoving Submissions from '{submissions_category.parent.name}' to '{year_2026.name}'...")
submissions_category.parent = year_2026
submissions_category.save()

print("✓ Moved successfully!")

# Verify the new structure
print("\n" + "=" * 60)
print("NEW STRUCTURE UNDER MAIN ROOT")
print("=" * 60)

print(f"\n{main_root.name} (ID: {main_root.id})")
for child in main_root.children.all():
    print(f"  └─ {child.name} ({child.folder_type}) - ID: {child.id}")
    for grandchild in child.children.all():
        print(f"      └─ {grandchild.name} ({grandchild.folder_type}) - ID: {grandchild.id}")

# Check if Document Tracking ROOT is now empty
doc_tracking_root = DocumentFolder.objects.get(id=83, name="Document Tracking")
print(f"\n{doc_tracking_root.name} (ID: {doc_tracking_root.id})")
print(f"  Children: {doc_tracking_root.children.count()}")

if doc_tracking_root.children.count() == 0:
    print("\n⚠ Document Tracking ROOT is now empty. You may want to delete it.")
    print("  To delete: DocumentFolder.objects.get(id=83).delete()")

print("\n" + "=" * 60)
