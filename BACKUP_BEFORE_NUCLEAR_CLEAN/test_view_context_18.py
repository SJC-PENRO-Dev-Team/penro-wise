"""
Test the view context for submission 18.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from collections import defaultdict

# Get submission 18
submission = Submission.objects.get(id=18)

# Simulate the view logic
link_groups = {}
single_links = []
file_attachments = []

if submission.primary_folder:
    temp_groups = defaultdict(list)
    
    for att in submission.primary_folder.files.all():
        print(f"Processing attachment {att.id}:")
        print(f"  link_url: {att.link_url}")
        print(f"  link_title: {att.link_title}")
        print(f"  file: {att.file}")
        print(f"  is_link(): {att.is_link()}")
        print(f"  is_file(): {att.is_file()}")
        
        if att.link_url:
            # It's a link
            if att.link_title:
                temp_groups[att.link_title].append(att)
                print(f"  → Added to temp_groups['{att.link_title}']")
            else:
                single_links.append(att)
                print(f"  → Added to single_links (no title)")
        else:
            # It's a file
            file_attachments.append(att)
            print(f"  → Added to file_attachments")
        print()
    
    # Separate grouped links (multiple with same title) from single links
    for title, links in temp_groups.items():
        print(f"Checking temp_group '{title}': {len(links)} link(s)")
        if len(links) > 1:
            link_groups[title] = links
            print(f"  → Added to link_groups (multiple links)")
        else:
            single_links.extend(links)
            print(f"  → Moved to single_links (only one link)")
        print()

print("="*60)
print("FINAL CONTEXT:")
print("="*60)
print(f"link_groups: {len(link_groups)} groups")
for title, links in link_groups.items():
    print(f"  '{title}': {len(links)} links")

print(f"\nsingle_links: {len(single_links)} links")
for link in single_links:
    print(f"  '{link.link_title}': {link.link_url}")

print(f"\nfile_attachments: {len(file_attachments)} files")
for file in file_attachments:
    print(f"  {file.get_filename()}")

print("\n" + "="*60)
print("TEMPLATE WILL DISPLAY:")
print("="*60)
if link_groups or single_links or file_attachments:
    print("✓ Attachments section will show")
    if link_groups:
        print(f"  - {len(link_groups)} grouped link section(s)")
    if single_links:
        print(f"  - {len(single_links)} single link item(s)")
    if file_attachments:
        print(f"  - {len(file_attachments)} file item(s)")
else:
    print("✗ 'No files or links attached' message")
