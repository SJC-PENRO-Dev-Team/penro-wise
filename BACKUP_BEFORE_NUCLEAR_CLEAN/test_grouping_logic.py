"""
Test the grouping logic for folder 75
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder
from collections import defaultdict

# Get folder 75
folder = DocumentFolder.objects.get(id=75)
print(f"Folder: {folder.name} (ID: {folder.id})")
print()

# Get all attachments in this folder
attachments = WorkItemAttachment.objects.filter(
    acceptance_status="accepted",
    folder=folder
).select_related("work_item", "uploaded_by")

print(f"Total attachments: {attachments.count()}")
print()

# Group links by link_title (same logic as the view)
grouped_links = defaultdict(list)
files = []

for attachment in attachments:
    if attachment.is_link() and attachment.link_title:
        # Group links by their title
        grouped_links[attachment.link_title].append(attachment)
    else:
        # Regular files and links without titles
        files.append(attachment)

print(f"Grouped links: {len(grouped_links)} groups")
print(f"Individual files: {len(files)}")
print()

# Convert grouped_links to a list of dicts for template
link_groups = []
for group_name, links in grouped_links.items():
    if len(links) > 1:
        # Multiple links with same title - create a group
        link_groups.append({
            'name': group_name,
            'count': len(links),
            'links': links,
            'first_link': links[0],
        })
        print(f"Group: '{group_name}' - {len(links)} links")
    else:
        # Single link - treat as individual file
        files.append(links[0])
        print(f"Individual link: '{group_name}' - 1 link")

print()
print(f"Final link_groups count: {len(link_groups)}")
print(f"Final files count: {len(files)}")
