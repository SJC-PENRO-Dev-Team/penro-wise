"""
Check submission 17 and its links.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment

# Get submission 17
try:
    submission = Submission.objects.get(id=17)
    print(f"Submission #{submission.id}: {submission.title}")
    print(f"Status: {submission.status}")
    print(f"Primary Folder: {submission.primary_folder}")
    
    if submission.primary_folder:
        print(f"\nPrimary Folder ID: {submission.primary_folder.id}")
        print(f"Primary Folder Path: {submission.primary_folder.get_path_string()}")
        
        # Get all files in the folder
        files = submission.primary_folder.files.all()
        print(f"\nTotal attachments in folder: {files.count()}")
        
        for att in files:
            print(f"\n  Attachment ID: {att.id}")
            print(f"  Type: {att.attachment_type}")
            if att.file:
                print(f"  File: {att.file.name}")
            if att.link_url:
                print(f"  Link URL: {att.link_url}")
                print(f"  Link Title: {att.link_title}")
            print(f"  Uploaded by: {att.uploaded_by}")
            print(f"  Uploaded at: {att.uploaded_at}")
    else:
        print("\nNo primary folder assigned!")
        
except Submission.DoesNotExist:
    print("Submission 17 not found!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
