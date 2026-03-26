import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItem, WorkItemAttachment

# Check work item 51
work_item = WorkItem.objects.filter(id=51).first()
if work_item:
    print(f"Work Item: {work_item}")
    print(f"Owner: {work_item.owner}")
    
    # Get all attachments
    attachments = work_item.attachments.all()
    print(f"\nTotal attachments: {attachments.count()}")
    
    for att in attachments:
        print(f"\n--- Attachment ID: {att.id} ---")
        print(f"Type: {att.attachment_type}")
        print(f"Is Link: {att.is_link()}")
        print(f"Link URL: {att.link_url}")
        print(f"Link Title: {att.link_title}")
        print(f"File: {att.file}")
        print(f"Acceptance Status: {att.acceptance_status}")
        print(f"Uploaded At: {att.uploaded_at}")
else:
    print("Work item 51 not found")
