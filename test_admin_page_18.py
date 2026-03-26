import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission

submission = Submission.objects.get(id=18)

print(f"Submission ID: {submission.id}")
print(f"Primary Folder: {submission.primary_folder}")
print(f"Primary Folder ID: {submission.primary_folder.id if submission.primary_folder else 'None'}")

if submission.primary_folder:
    attachments = submission.primary_folder.files.all()
    print(f"\nTotal attachments: {attachments.count()}")
    
    for att in attachments:
        print(f"\nAttachment ID: {att.id}")
        print(f"  - link_url: {att.link_url}")
        print(f"  - link_title: {att.link_title}")
        print(f"  - file: {att.file}")

# Test the API endpoint
print("\n=== TESTING API ENDPOINT ===")
folder_id = submission.primary_folder.id
group_name = "fucking ehll"

print(f"\nAPI URL would be: /admin/documents/files/grouped-links/{folder_id}/{group_name}/")

# Simulate what the API should return
from collections import defaultdict
link_groups = defaultdict(list)

for att in submission.primary_folder.files.all():
    if att.link_url and att.link_title:
        link_groups[att.link_title].append({
            'id': att.id,
            'url': att.link_url,
            'title': att.link_title
        })

print(f"\nLink groups: {dict(link_groups)}")
print(f"Group '{group_name}' has {len(link_groups.get(group_name, []))} links")
