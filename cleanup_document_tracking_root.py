#!/usr/bin/env python
"""Clean up the Document Tracking ROOT"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder

print("=" * 60)
print("CLEANING UP DOCUMENT TRACKING ROOT")
print("=" * 60)

# Get Document Tracking ROOT and its children
doc_tracking_root = DocumentFolder.objects.get(id=83, name="Document Tracking")
print(f"\nDocument Tracking ROOT (ID: {doc_tracking_root.id})")
print(f"Children: {doc_tracking_root.children.count()}")

for child in doc_tracking_root.children.all():
    print(f"  - {child.name} ({child.folder_type}) - ID: {child.id}")
    print(f"    Has {child.children.count()} children")

# Delete the orphaned 2026 year folder first
orphaned_year = DocumentFolder.objects.get(id=84, parent=doc_tracking_root)
print(f"\nDeleting orphaned year folder: {orphaned_year.name} (ID: {orphaned_year.id})")
orphaned_year.delete()
print("✓ Deleted")

# Delete the Document Tracking ROOT
print(f"\nDeleting Document Tracking ROOT (ID: {doc_tracking_root.id})")
doc_tracking_root.delete()
print("✓ Deleted")

# Verify final structure
print("\n" + "=" * 60)
print("FINAL STRUCTURE")
print("=" * 60)

main_root = DocumentFolder.objects.get(id=10, name="ROOT")
print(f"\n{main_root.name} (ID: {main_root.id})")
for child in main_root.children.all():
    print(f"  └─ {child.name} ({child.folder_type}) - ID: {child.id}")
    for grandchild in child.children.all():
        print(f"      └─ {grandchild.name} ({grandchild.folder_type}) - ID: {grandchild.id}")

print(f"\nTotal ROOT folders: {DocumentFolder.objects.filter(folder_type='root').count()}")

print("\n" + "=" * 60)
