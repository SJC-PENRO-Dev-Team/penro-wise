"""
Fix acceptance_status for submission links that are currently 'pending'.

This script updates all WorkItemAttachment records that:
1. Are link attachments (link_url is not null)
2. Have attachment_type='document' (submission attachments)
3. Have acceptance_status='pending' (should be 'accepted')
4. Are in folders associated with approved submissions

This fixes the bug where submission links were created without acceptance_status='accepted',
causing them to be hidden in File Manager view.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from document_tracking.models import Submission
from django.db.models import Q

print("=" * 80)
print("FIX: Submission Link Acceptance Status")
print("=" * 80)

# Find all submission links with pending status
pending_links = WorkItemAttachment.objects.filter(
    link_url__isnull=False,  # Is a link
    attachment_type='document',  # Submission attachment
    acceptance_status='pending',  # Currently pending
    work_item__isnull=True  # Not a WorkItem attachment
)

print(f"\nFound {pending_links.count()} submission links with 'pending' status")

if pending_links.count() == 0:
    print("\n✓ No links need fixing!")
    exit(0)

# Show details
print("\nLinks to be updated:")
for link in pending_links:
    print(f"  - ID {link.id}: {link.link_title or 'Untitled'}")
    print(f"    URL: {link.link_url}")
    print(f"    Folder: {link.folder.name if link.folder else 'None'}")
    
    # Check if this link is in a submission folder
    if link.folder:
        # Check if folder is linked to any submission
        submission = Submission.objects.filter(
            Q(primary_folder=link.folder) |
            Q(file_manager_folder=link.folder)
        ).first()
        
        if submission:
            print(f"    Submission: #{submission.id} - {submission.title} ({submission.status})")
        else:
            print(f"    Submission: Not found")
    print()

# Ask for confirmation
response = input("\nUpdate all these links to 'accepted' status? (yes/no): ")

if response.lower() != 'yes':
    print("\n✗ Cancelled")
    exit(0)

# Update links
updated_count = pending_links.update(acceptance_status='accepted')

print(f"\n✓ Updated {updated_count} links to 'accepted' status")
print("\nThese links should now be visible in File Manager view.")

print("\n" + "=" * 80)
print("VERIFICATION")
print("=" * 80)

# Verify the fix
remaining_pending = WorkItemAttachment.objects.filter(
    link_url__isnull=False,
    attachment_type='document',
    acceptance_status='pending',
    work_item__isnull=True
).count()

print(f"\nRemaining pending submission links: {remaining_pending}")

if remaining_pending == 0:
    print("✓ All submission links are now 'accepted'")
else:
    print(f"⚠ Warning: {remaining_pending} links still pending")

print("\n" + "=" * 80)
