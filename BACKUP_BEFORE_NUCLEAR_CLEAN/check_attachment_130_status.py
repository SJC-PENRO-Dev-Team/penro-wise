import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment

att = WorkItemAttachment.objects.get(id=130)

print(f"Attachment ID: {att.id}")
print(f"Link URL: {att.link_url}")
print(f"Link Title: {att.link_title}")
print(f"Acceptance Status: {att.acceptance_status}")
print(f"Folder: {att.folder}")
print(f"Folder ID: {att.folder.id}")
print(f"Uploaded By: {att.uploaded_by}")

# Check what the API query would return
from accounts.models import DocumentFolder

folder = DocumentFolder.objects.get(id=115)
group_name = "fucking ehll"

links = WorkItemAttachment.objects.filter(
    acceptance_status="accepted",
    folder=folder,
    link_title=group_name,
    link_url__isnull=False
)

print(f"\n=== API QUERY RESULT ===")
print(f"Query: acceptance_status='accepted', folder={folder.id}, link_title='{group_name}'")
print(f"Count: {links.count()}")

# Try without acceptance_status filter
links_all = WorkItemAttachment.objects.filter(
    folder=folder,
    link_title=group_name,
    link_url__isnull=False
)

print(f"\n=== WITHOUT acceptance_status FILTER ===")
print(f"Count: {links_all.count()}")
for link in links_all:
    print(f"  - ID: {link.id}, Status: {link.acceptance_status}")
