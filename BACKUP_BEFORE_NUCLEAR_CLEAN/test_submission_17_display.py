"""
Test if submission 17 displays correctly with the new view logic.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from collections import defaultdict

# Get submission 17
submission = Submission.objects.get(id=17)
print(f"Submission #{submission.id}: {submission.title}\n")

# Simulate the view logic
link_groups = {}
single_links = []
file_attachments = []

if submission.primary_folder:
    temp_groups = defaultdict(list)
    
    for att in submission.primary_folder.files.all():
        if att.link_url:
            # It's a link
            if att.link_title:
                temp_groups[att.link_title].append(att)
            else:
                single_links.append(att)
        else:
            # It's a file
            file_attachments.append(att)
    
    # Separate grouped links (multiple with same title) from single links
    for title, links in temp_groups.items():
        if len(links) > 1:
            link_groups[title] = links
        else:
            single_links.extend(links)

print("="*60)
print("DISPLAY LOGIC RESULTS:")
print("="*60)

print(f"\nGrouped Links: {len(link_groups)}")
for title, links in link_groups.items():
    print(f"  '{title}': {len(links)} links")
    for link in links:
        print(f"    - {link.link_url}")

print(f"\nSingle Links: {len(single_links)}")
for link in single_links:
    print(f"  '{link.link_title}': {link.link_url}")

print(f"\nFile Attachments: {len(file_attachments)}")
for file in file_attachments:
    print(f"  {file.get_filename()}")

print("\n" + "="*60)
print("EXPECTED DISPLAY:")
print("="*60)
print("The page should show:")
print("  - 1 single link: 'hi' -> https://brother.com")
print("  - 0 grouped links")
print("  - 0 file attachments")
