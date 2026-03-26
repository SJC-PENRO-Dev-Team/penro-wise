#!/usr/bin/env python
"""Check folder structure in database"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder
from accounts.models import WorkCycle

print("=" * 60)
print("FOLDER STRUCTURE ANALYSIS")
print("=" * 60)

print(f"\nTotal folders: {DocumentFolder.objects.count()}")
print(f"ROOT folders: {DocumentFolder.objects.filter(folder_type='root').count()}")
print(f"YEAR folders: {DocumentFolder.objects.filter(folder_type='year').count()}")
print(f"CATEGORY folders: {DocumentFolder.objects.filter(folder_type='category').count()}")
print(f"WORKCYCLE folders: {DocumentFolder.objects.filter(folder_type='workcycle').count()}")
print(f"Total WorkCycles: {WorkCycle.objects.count()}")

print("\n" + "=" * 60)
print("FOLDER HIERARCHY (first 30 folders)")
print("=" * 60)

for folder in DocumentFolder.objects.all().order_by('folder_type', 'name')[:30]:
    parent_name = folder.parent.name if folder.parent else "None"
    workcycle_id = folder.workcycle.id if folder.workcycle else "None"
    print(f"{folder.folder_type:12} | {folder.name:30} | Parent: {parent_name:20} | WC_ID: {workcycle_id}")

print("\n" + "=" * 60)
print("WORKCYCLE DETAILS")
print("=" * 60)

for wc in WorkCycle.objects.all()[:10]:
    folder_count = wc.folders.count()
    print(f"WorkCycle ID: {wc.id} - {folder_count} folders")
    if folder_count > 0:
        for folder in wc.folders.all()[:5]:
            print(f"  - {folder.name} ({folder.folder_type})")

print("\n" + "=" * 60)
