"""
Check how links are grouped in submission 17.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import WorkItemAttachment
from django.db.models import Count

# Get submission 17
submission = Submission.objects.get(id=17)
print(f"Submission #{submission.id}: {submission.title}")
print(f"Primary Folder ID: {submission.primary_folder.id}\n")

# Get all link attachments in the folder
links = WorkItemAttachment.objects.filter(
    folder=submission.primary_folder,
    link_url__isnull=False
)

print(f"Total link attachments: {links.count()}\n")

# Group by title
from collections import defaultdict
grouped = defaultdict(list)

for link in links:
    grouped[link.link_title].append(link)

print("Links grouped by title:")
for title, link_list in grouped.items():
    print(f"\n  Title: '{title}'")
    print(f"  Count: {len(link_list)}")
    for link in link_list:
        print(f"    - {link.link_url}")

# Check if any title has multiple links
print("\n" + "="*60)
for title, link_list in grouped.items():
    if len(link_list) > 1:
        print(f"GROUPED: '{title}' has {len(link_list)} links")
    else:
        print(f"SINGLE: '{title}' has 1 link")
