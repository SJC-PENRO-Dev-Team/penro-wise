"""
Investigation script for submission 11 links issue.
Checks database state and relationships.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder

print("=" * 80)
print("INVESTIGATION: Submission 11 Links Missing in File Manager")
print("=" * 80)

# Get submission 11
try:
    submission = Submission.objects.get(id=11)
    print(f"\n✓ Found Submission #{submission.id}")
    print(f"  Title: {submission.title}")
    print(f"  Status: {submission.status}")
    print(f"  Tracking: {submission.tracking_number}")
    print(f"  Is stored in File Manager: {submission.is_stored_in_file_manager}")
except Submission.DoesNotExist:
    print("\n✗ Submission 11 not found!")
    exit(1)

print("\n" + "=" * 80)
print("FOLDER RELATIONSHIPS")
print("=" * 80)

# Check primary folder
if submission.primary_folder:
    print(f"\n✓ Primary Folder: ID={submission.primary_folder.id}")
    print(f"  Name: {submission.primary_folder.name}")
    
    # Get attachments in primary folder
    attachments = submission.primary_folder.files.all()
    print(f"\n  Attachments in Primary Folder: {attachments.count()}")
    
    for att in attachments:
        if att.link_url:
            print(f"    - LINK: {att.link_title or 'Untitled'}")
            print(f"      URL: {att.link_url}")
            print(f"      ID: {att.id}")
            print(f"      Folder ID: {att.folder_id}")
        else:
            print(f"    - FILE: {att.file_name}")
            print(f"      ID: {att.id}")
            print(f"      Folder ID: {att.folder_id}")
else:
    print("\n✗ No primary folder!")

# Check file manager folder
if submission.file_manager_folder:
    print(f"\n✓ File Manager Folder: ID={submission.file_manager_folder.id}")
    print(f"  Name: {submission.file_manager_folder.name}")
    
    # Get attachments in file manager folder
    attachments = submission.file_manager_folder.files.all()
    print(f"\n  Attachments in File Manager Folder: {attachments.count()}")
    
    for att in attachments:
        if att.link_url:
            print(f"    - LINK: {att.link_title or 'Untitled'}")
            print(f"      URL: {att.link_url}")
            print(f"      ID: {att.id}")
            print(f"      Folder ID: {att.folder_id}")
        else:
            print(f"    - FILE: {att.file_name}")
            print(f"      ID: {att.id}")
            print(f"      Folder ID: {att.folder_id}")
else:
    print("\n✗ No file manager folder!")

# Check archive folder (deprecated but might exist)
if submission.archive_folder:
    print(f"\n⚠ Archive Folder (deprecated): ID={submission.archive_folder.id}")
    print(f"  Name: {submission.archive_folder.name}")
    attachments = submission.archive_folder.files.all()
    print(f"  Attachments: {attachments.count()}")

print("\n" + "=" * 80)
print("ALL ATTACHMENTS FOR THIS SUBMISSION")
print("=" * 80)

# Find all attachments that might be related
all_attachments = WorkItemAttachment.objects.filter(
    folder__in=[
        submission.primary_folder,
        submission.file_manager_folder,
        submission.archive_folder
    ]
).exclude(folder=None)

print(f"\nTotal attachments found: {all_attachments.count()}")

for att in all_attachments:
    print(f"\n  Attachment ID: {att.id}")
    print(f"  Type: {'LINK' if att.link_url else 'FILE'}")
    if att.link_url:
        print(f"  Title: {att.link_title}")
        print(f"  URL: {att.link_url}")
    else:
        print(f"  File: {att.file_name}")
    print(f"  Folder ID: {att.folder_id}")
    print(f"  Folder Name: {att.folder.name if att.folder else 'None'}")
    print(f"  Uploaded By: {att.uploaded_by.get_full_name() if att.uploaded_by else 'Unknown'}")

print("\n" + "=" * 80)
print("FOLDER 21 INVESTIGATION (File Manager View)")
print("=" * 80)

try:
    folder_21 = DocumentFolder.objects.get(id=21)
    print(f"\n✓ Found Folder #{folder_21.id}")
    print(f"  Name: {folder_21.name}")
    print(f"  Parent: {folder_21.parent.name if folder_21.parent else 'ROOT'}")
    
    # Check if this is the file manager folder
    if submission.file_manager_folder and submission.file_manager_folder.id == 21:
        print(f"  ✓ This IS the file manager folder for submission 11")
    elif submission.primary_folder and submission.primary_folder.id == 21:
        print(f"  ⚠ This is the PRIMARY folder, not file manager folder")
    else:
        print(f"  ✗ This folder is NOT linked to submission 11")
    
    # Get attachments
    attachments = folder_21.files.all()
    print(f"\n  Attachments in Folder 21: {attachments.count()}")
    
    for att in attachments:
        if att.link_url:
            print(f"    - LINK: {att.link_title or 'Untitled'}")
            print(f"      URL: {att.link_url}")
        else:
            print(f"    - FILE: {att.file_name}")
            
except DocumentFolder.DoesNotExist:
    print("\n✗ Folder 21 not found!")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

# Determine the issue
if submission.primary_folder and submission.file_manager_folder:
    primary_links = submission.primary_folder.files.filter(link_url__isnull=False).count()
    fm_links = submission.file_manager_folder.files.filter(link_url__isnull=False).count()
    
    print(f"\nLinks in Primary Folder: {primary_links}")
    print(f"Links in File Manager Folder: {fm_links}")
    
    if primary_links > 0 and fm_links == 0:
        print("\n⚠ ISSUE CONFIRMED: Links exist in primary folder but NOT in file manager folder")
        print("   This means the approval process did not transfer/copy links.")
    elif primary_links == 0 and fm_links == 0:
        print("\n⚠ No links found in either folder - submission may not have had links")
    elif fm_links > 0:
        print("\n✓ Links exist in file manager folder - no issue detected")

print("\n" + "=" * 80)
