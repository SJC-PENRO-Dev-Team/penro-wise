import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import DocumentFolder, WorkItemAttachment

folder = DocumentFolder.objects.get(id=115)
group_name = "fucking ehll"

print(f"Folder: {folder}")
print(f"Folder Type: {folder.folder_type}")

# Simulate the fixed API logic
query = WorkItemAttachment.objects.filter(
    folder=folder,
    link_title=group_name,
    link_url__isnull=False
)

# Only filter by acceptance_status for file manager folders (not document tracking)
if folder.folder_type != 'attachment':
    query = query.filter(acceptance_status="accepted")
    print("Filtering by acceptance_status='accepted'")
else:
    print("NOT filtering by acceptance_status (document tracking folder)")

links = query.select_related("uploaded_by").order_by('uploaded_at')

print(f"\nQuery result count: {links.count()}")

for link in links:
    print(f"\nLink ID: {link.id}")
    print(f"  URL: {link.link_url}")
    print(f"  Title: {link.link_title}")
    print(f"  Status: {link.acceptance_status}")
    print(f"  Uploaded by: {link.uploaded_by.get_full_name()}")
