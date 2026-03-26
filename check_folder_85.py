#!/usr/bin/env python
"""Check folder 85 details"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder
from accounts.models import WorkItemAttachment

print("=" * 60)
print("FOLDER 85 ANALYSIS")
print("=" * 60)

try:
    folder = DocumentFolder.objects.get(id=85)
    print(f"\nFolder ID: {folder.id}")
    print(f"Name: {folder.name}")
    print(f"Type: {folder.folder_type}")
    print(f"Parent: {folder.parent.name if folder.parent else 'None'} (ID: {folder.parent.id if folder.parent else 'None'})")
    print(f"System Generated: {folder.is_system_generated}")
    print(f"Workcycle: {folder.workcycle.id if folder.workcycle else 'None'}")
    
    print("\n" + "=" * 60)
    print("PATH TO THIS FOLDER")
    print("=" * 60)
    path = folder.get_path()
    for i, p in enumerate(path):
        indent = "  " * i
        print(f"{indent}{p.name} ({p.folder_type}) - ID: {p.id}")
    
    print("\n" + "=" * 60)
    print("CHILDREN FOLDERS")
    print("=" * 60)
    children = folder.children.all()
    print(f"Total children: {children.count()}")
    for child in children:
        print(f"  - {child.name} ({child.folder_type}) - ID: {child.id}")
    
    print("\n" + "=" * 60)
    print("FILES IN THIS FOLDER")
    print("=" * 60)
    files = WorkItemAttachment.objects.filter(folder=folder, acceptance_status='accepted')
    print(f"Total files: {files.count()}")
    for file in files[:10]:
        print(f"  - {file.get_filename()} (Type: {file.attachment_type})")
    
except DocumentFolder.DoesNotExist:
    print("\nERROR: Folder with ID 85 does not exist!")
    print("\nAll folder IDs in database:")
    for f in DocumentFolder.objects.all().order_by('id'):
        print(f"  ID {f.id}: {f.name} ({f.folder_type})")

print("\n" + "=" * 60)
