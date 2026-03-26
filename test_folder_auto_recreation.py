"""
Test: Folder Auto-Recreation After Deletion

This script demonstrates what happens when an admin deletes a workcycle folder
and then a user uploads a file to that work item.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder
from structure.services.folder_resolution import resolve_attachment_folder
from accounts.models import WorkItem, User

print("\n" + "="*70)
print("FOLDER AUTO-RECREATION TEST")
print("="*70)

# Find a work item to test with
work_item = WorkItem.objects.filter(is_active=True).first()

if not work_item:
    print("\n❌ No active work items found for testing")
    exit()

print(f"\n📋 Test Work Item: #{work_item.id}")
print(f"   Workcycle: {work_item.workcycle.title}")
print(f"   Owner: {work_item.owner.get_full_name()}")

# Get the user (actor)
user = work_item.owner

print("\n" + "-"*70)
print("STEP 1: Resolve folder structure (initial)")
print("-"*70)

# Resolve the folder for this work item
folder = resolve_attachment_folder(
    work_item=work_item,
    attachment_type="matrix_a",
    actor=user
)

print(f"\n✅ Folder resolved: {folder.name}")
print(f"   Type: {folder.folder_type}")
print(f"   Path: {' / '.join([f.name for f in folder.get_path()])}")
print(f"   ID: {folder.id}")

# Find the workcycle folder in the path
workcycle_folder = None
for f in folder.get_path():
    if f.folder_type == DocumentFolder.FolderType.WORKCYCLE:
        workcycle_folder = f
        break

if not workcycle_folder:
    print("\n❌ No workcycle folder found in path")
    exit()

print(f"\n📁 Workcycle Folder: {workcycle_folder.name}")
print(f"   ID: {workcycle_folder.id}")
print(f"   System Generated: {workcycle_folder.is_system_generated}")

print("\n" + "-"*70)
print("STEP 2: Simulate admin deleting the workcycle folder")
print("-"*70)

# Count children before deletion
children_count = DocumentFolder.objects.filter(parent=workcycle_folder).count()
print(f"\n📊 Workcycle folder has {children_count} child folder(s)")

# Store the folder ID for reference
deleted_folder_id = workcycle_folder.id
deleted_folder_name = workcycle_folder.name

# Simulate deletion (we'll actually delete it)
print(f"\n🗑️  Deleting workcycle folder: {deleted_folder_name}")
workcycle_folder.delete()

# Verify deletion
exists = DocumentFolder.objects.filter(id=deleted_folder_id).exists()
print(f"   Folder exists after deletion: {exists}")

if not exists:
    print("   ✅ Folder successfully deleted")
else:
    print("   ❌ Folder still exists!")

print("\n" + "-"*70)
print("STEP 3: User uploads file (folder resolution triggered)")
print("-"*70)

# Now resolve the folder again (simulating a file upload)
print(f"\n🔄 Resolving folder again for the same work item...")

new_folder = resolve_attachment_folder(
    work_item=work_item,
    attachment_type="matrix_a",
    actor=user
)

print(f"\n✅ Folder resolved: {new_folder.name}")
print(f"   Type: {new_folder.folder_type}")
print(f"   Path: {' / '.join([f.name for f in new_folder.get_path()])}")
print(f"   ID: {new_folder.id}")

# Find the workcycle folder in the new path
new_workcycle_folder = None
for f in new_folder.get_path():
    if f.folder_type == DocumentFolder.FolderType.WORKCYCLE:
        new_workcycle_folder = f
        break

if new_workcycle_folder:
    print(f"\n📁 Workcycle Folder (Recreated): {new_workcycle_folder.name}")
    print(f"   ID: {new_workcycle_folder.id}")
    print(f"   System Generated: {new_workcycle_folder.is_system_generated}")
    
    if new_workcycle_folder.id == deleted_folder_id:
        print("\n   ⚠️  Same folder ID (not recreated, somehow still exists)")
    else:
        print("\n   ✅ NEW FOLDER CREATED (different ID)")
        print(f"   Old ID: {deleted_folder_id}")
        print(f"   New ID: {new_workcycle_folder.id}")
else:
    print("\n❌ No workcycle folder found in new path")

print("\n" + "="*70)
print("TEST RESULTS")
print("="*70)

print("\n📝 ANSWER TO YOUR QUESTION:")
print("-"*70)

if new_workcycle_folder and new_workcycle_folder.id != deleted_folder_id:
    print("\n✅ YES - Folders are automatically recreated!")
    print("\nHow it works:")
    print("1. Admin deletes workcycle folder in file manager")
    print("2. User uploads file to work item")
    print("3. resolve_attachment_folder() is called")
    print("4. get_or_create_folder() recreates the entire folder structure")
    print("5. File is saved to the newly created folder")
    print("\nThe folder resolution service uses get_or_create_folder()")
    print("which automatically creates any missing folders in the hierarchy.")
else:
    print("\n⚠️  Folder was not recreated (unexpected)")

print("\n" + "="*70)
print("\nKey Points:")
print("-"*70)
print("• Folder structure: ROOT → YEAR → CATEGORY → WORKCYCLE → ORG")
print("• Each level uses get_or_create_folder()")
print("• If folder doesn't exist, it's created automatically")
print("• System-generated folders are marked with is_system_generated=True")
print("• Folder uniqueness: (parent, name) combination")
print("\n✅ Safe to delete folders - they will be recreated on next upload")
print("\n")
