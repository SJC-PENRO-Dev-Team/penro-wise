#!/usr/bin/env python
"""
Test script to check if links are being saved in document submissions.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment

print("=" * 80)
print("CHECKING LINK SUBMISSIONS")
print("=" * 80)

# Get the most recent submission
try:
    submission = Submission.objects.latest('created_at')
    print(f"\nMost recent submission:")
    print(f"  ID: {submission.id}")
    print(f"  Title: {submission.title}")
    print(f"  Submitted by: {submission.submitted_by.get_full_name()}")
    print(f"  Created: {submission.created_at}")
    
    if submission.primary_folder:
        print(f"\n  Primary Folder ID: {submission.primary_folder.id}")
        
        # Check all attachments
        attachments = submission.primary_folder.files.all()
        print(f"  Total attachments: {attachments.count()}")
        
        files_count = 0
        links_count = 0
        
        for att in attachments:
            if att.link_url:
                links_count += 1
                print(f"\n  Link #{links_count}:")
                print(f"    Title: {att.link_title}")
                print(f"    URL: {att.link_url}")
                print(f"    Type: {att.attachment_type}")
            else:
                files_count += 1
                print(f"\n  File #{files_count}:")
                print(f"    Name: {att.get_filename()}")
        
        print(f"\n  Summary: {files_count} files, {links_count} links")
        
        if links_count == 0:
            print("\n  ⚠️  NO LINKS FOUND!")
            print("  This indicates links are not being saved properly.")
    else:
        print("\n  ✗ No primary folder")
        
except Submission.DoesNotExist:
    print("\n✗ No submissions found")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
