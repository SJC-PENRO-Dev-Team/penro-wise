"""
Delete all WorkCycles and DocumentFolders.
This will cascade delete all related data (WorkItems, Attachments, etc.)

Usage: python delete_workcycles_and_folders.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.db import transaction
from accounts.models import WorkCycle
from structure.models import DocumentFolder

print("=" * 60)
print("DELETE WORKCYCLES AND DOCUMENT FOLDERS")
print("=" * 60)
print()

# Count records
workcycle_count = WorkCycle.objects.count()
folder_count = DocumentFolder.objects.count()

print(f"WorkCycles: {workcycle_count}")
print(f"Document Folders: {folder_count}")
print()

if workcycle_count == 0 and folder_count == 0:
    print("✅ Nothing to delete!")
    exit(0)

print("⚠️  This will also delete:")
print("  - All WorkItems")
print("  - All WorkAssignments")
print("  - All Attachments")
print("  - All Messages")
print("  - All related data")
print()

confirm = input("Type 'DELETE' to confirm: ")

if confirm != 'DELETE':
    print("❌ Cancelled")
    exit(0)

print()
print("🗑️  Deleting...")
print()

try:
    with transaction.atomic():
        # Delete WorkCycles (cascades to WorkItems, Attachments, etc.)
        if workcycle_count > 0:
            WorkCycle.objects.all().delete()
            print(f"✅ Deleted {workcycle_count} WorkCycles")
        
        # Delete DocumentFolders
        if folder_count > 0:
            DocumentFolder.objects.all().delete()
            print(f"✅ Deleted {folder_count} Document Folders")
        
        print()
        print("=" * 60)
        print("✅ DELETION COMPLETE!")
        print("=" * 60)
        
except Exception as e:
    print()
    print(f"❌ Error: {str(e)}")
    print("Transaction rolled back - nothing was deleted")
    raise
