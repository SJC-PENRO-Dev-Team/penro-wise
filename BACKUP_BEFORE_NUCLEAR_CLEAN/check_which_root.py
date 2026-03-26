#!/usr/bin/env python
"""Check which ROOT the file manager uses"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder

print("=" * 60)
print("ROOT FOLDERS IN DATABASE")
print("=" * 60)

roots = DocumentFolder.objects.filter(folder_type='root', parent__isnull=True)
print(f"\nTotal ROOT folders: {roots.count()}")

for root in roots:
    print(f"\n{'='*60}")
    print(f"ROOT: {root.name} (ID: {root.id})")
    print(f"{'='*60}")
    
    children = root.children.all()
    print(f"Direct children: {children.count()}")
    for child in children:
        print(f"  - {child.name} ({child.folder_type}) - ID: {child.id}")
        
        # Show grandchildren
        grandchildren = child.children.all()
        if grandchildren.count() > 0:
            print(f"    Children of {child.name}:")
            for gc in grandchildren:
                print(f"      - {gc.name} ({gc.folder_type}) - ID: {gc.id}")

print("\n" + "=" * 60)
print("FILE MANAGER DEFAULT QUERY")
print("=" * 60)

# This is what the file manager does
default_root = DocumentFolder.objects.filter(
    folder_type=DocumentFolder.FolderType.ROOT,
    parent__isnull=True
).first()

print(f"\nfile_manager_view() gets: {default_root.name} (ID: {default_root.id})")
print(f"This ROOT has {default_root.children.count()} children")

print("\n" + "=" * 60)
