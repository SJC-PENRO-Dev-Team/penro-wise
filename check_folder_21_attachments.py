"""
Check all attachments in folder 21 (File Manager view).
Shows IDs, types, acceptance status, and other details.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder

print("=" * 80)
print("FOLDER 21 ATTACHMENTS CHECK")
print("=" * 80)

# Get folder 21
try:
    folder = DocumentFolder.objects.get(id=21)
    print(f"\n✓ Folder #{folder.id}: {folder.name}")
    print(f"  Type: {folder.get_folder_type_display()}")
    print(f"  Parent: {folder.parent.name if folder.parent else 'ROOT'}")
except DocumentFolder.DoesNotExist:
    print("\n✗ Folder 21 not found!")
    exit(1)

print("\n" + "=" * 80)
print("ALL ATTACHMENTS IN FOLDER 21")
print("=" * 80)

# Get ALL attachments in folder 21 (no filters)
all_attachments = WorkItemAttachment.objects.filter(folder=folder).order_by('id')

print(f"\nTotal attachments: {all_attachments.count()}")

if all_attachments.count() == 0:
    print("\n⚠ No attachments found in this folder!")
else:
    for att in all_attachments:
        print(f"\n{'='*60}")
        print(f"Attachment ID: {att.id}")
        print(f"{'='*60}")
        
        # Type
        if att.link_url:
            print(f"Type: LINK")
            print(f"  Title: {att.link_title or 'Untitled'}")
            print(f"  URL: {att.link_url}")
        else:
            print(f"Type: FILE")
            print(f"  Filename: {att.get_filename()}")
            print(f"  File path: {att.file.name if att.file else 'None'}")
        
        # Status and metadata
        print(f"\nStatus & Metadata:")
        print(f"  Acceptance Status: {att.acceptance_status} {'✓' if att.acceptance_status == 'accepted' else '✗'}")
        print(f"  Attachment Type: {att.attachment_type}")
        print(f"  Work Item: {att.work_item.id if att.work_item else 'None (Standalone)'}")
        print(f"  Folder ID: {att.folder_id}")
        print(f"  Uploaded By: {att.uploaded_by.get_full_name() if att.uploaded_by else 'Unknown'}")
        print(f"  Uploaded At: {att.uploaded_at}")
        
        if att.acceptance_status == 'accepted':
            print(f"  Accepted At: {att.accepted_at or 'Not recorded'}")
        elif att.acceptance_status == 'rejected':
            print(f"  Rejected At: {att.rejected_at or 'Not recorded'}")
            print(f"  Rejection Reason: {att.rejection_reason or 'None'}")

print("\n" + "=" * 80)
print("FILTER SIMULATION (File Manager Query)")
print("=" * 80)

# Simulate File Manager query
accepted_attachments = WorkItemAttachment.objects.filter(
    folder=folder,
    acceptance_status='accepted'
)

print(f"\nAttachments with acceptance_status='accepted': {accepted_attachments.count()}")

if accepted_attachments.count() > 0:
    print("\nThese attachments WILL BE VISIBLE in File Manager:")
    for att in accepted_attachments:
        if att.link_url:
            print(f"  - ID {att.id}: LINK - {att.link_title or 'Untitled'}")
        else:
            print(f"  - ID {att.id}: FILE - {att.get_filename()}")
else:
    print("\n⚠ No attachments will be visible (all are pending/rejected)")

# Check for pending/rejected
non_accepted = WorkItemAttachment.objects.filter(
    folder=folder
).exclude(acceptance_status='accepted')

if non_accepted.count() > 0:
    print(f"\nAttachments that are HIDDEN (not accepted): {non_accepted.count()}")
    for att in non_accepted:
        if att.link_url:
            print(f"  - ID {att.id}: LINK - {att.link_title or 'Untitled'} (Status: {att.acceptance_status})")
        else:
            print(f"  - ID {att.id}: FILE - {att.get_filename()} (Status: {att.acceptance_status})")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if all_attachments.count() == 0:
    print("\n⚠ Folder is empty - no attachments at all")
elif accepted_attachments.count() == all_attachments.count():
    print("\n✓ All attachments are accepted - should be visible")
elif accepted_attachments.count() == 0:
    print("\n✗ NO attachments are accepted - nothing will be visible!")
    print("   Run: python fix_submission_link_acceptance_status.py")
else:
    print(f"\n⚠ Mixed status:")
    print(f"   Visible: {accepted_attachments.count()}")
    print(f"   Hidden: {non_accepted.count()}")

print("\n" + "=" * 80)
