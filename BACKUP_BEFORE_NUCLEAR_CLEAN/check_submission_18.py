"""
Check submission 18 and its attachments.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment

# Get submission 18
try:
    submission = Submission.objects.get(id=18)
    print(f"Submission #{submission.id}: {submission.title}")
    print(f"Status: {submission.status}")
    print(f"Submitted by: {submission.submitted_by}")
    print(f"Created at: {submission.created_at}")
    print(f"Primary Folder: {submission.primary_folder}")
    
    if submission.primary_folder:
        print(f"\nPrimary Folder ID: {submission.primary_folder.id}")
        print(f"Primary Folder Path: {submission.primary_folder.get_path_string()}")
        
        # Get all attachments in the folder
        attachments = submission.primary_folder.files.all()
        print(f"\nTotal attachments in folder: {attachments.count()}")
        
        if attachments.count() > 0:
            print("\n" + "="*60)
            print("ATTACHMENTS:")
            print("="*60)
            
            for att in attachments:
                print(f"\n  Attachment ID: {att.id}")
                print(f"  Type: {att.attachment_type}")
                
                if att.link_url:
                    print(f"  ✓ LINK ATTACHMENT")
                    print(f"    Link URL: {att.link_url}")
                    print(f"    Link Title: {att.link_title}")
                elif att.file:
                    print(f"  ✓ FILE ATTACHMENT")
                    print(f"    File: {att.file.name}")
                
                print(f"  Uploaded by: {att.uploaded_by}")
                print(f"  Uploaded at: {att.uploaded_at}")
        else:
            print("\n⚠ No attachments found in primary folder")
    else:
        print("\n⚠ No primary folder assigned!")
        
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    
    if submission.primary_folder:
        links = submission.primary_folder.files.filter(link_url__isnull=False)
        files = submission.primary_folder.files.filter(file__isnull=False)
        
        print(f"Total Links: {links.count()}")
        print(f"Total Files: {files.count()}")
        
        if links.count() > 0:
            print("\nLinks:")
            for link in links:
                print(f"  - '{link.link_title}': {link.link_url}")
        
        if files.count() > 0:
            print("\nFiles:")
            for file in files:
                print(f"  - {file.get_filename()}")
    
except Submission.DoesNotExist:
    print("❌ Submission 18 not found!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
