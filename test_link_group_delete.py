"""
Test script to debug link-group deletion
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder

# Get ROOT folder
root_folder = DocumentFolder.objects.filter(
    folder_type=DocumentFolder.FolderType.ROOT,
    parent__isnull=True
).first()

print(f"ROOT folder: {root_folder.name} (ID: {root_folder.id})")
print()

# Get all links in ROOT folder
links = WorkItemAttachment.objects.filter(
    acceptance_status="accepted",
    folder=root_folder,
    link_url__isnull=False
).order_by('link_title')

print(f"Total links in ROOT: {links.count()}")
print()

# Group by link_title
from collections import defaultdict
grouped = defaultdict(list)
for link in links:
    if link.link_title:
        grouped[link.link_title].append(link)

print("Grouped links:")
for title, link_list in grouped.items():
    print(f"  '{title}': {len(link_list)} links")
    for link in link_list:
        print(f"    - ID: {link.id}, URL: {link.link_url}")
print()

# Test what the frontend would send
print("Frontend would send for 'Projects' group:")
first_link = grouped['Projects'][0] if 'Projects' in grouped else None
if first_link:
    print(f"  type: 'link-group'")
    print(f"  id: {first_link.id}")
    print(f"  group_name: 'Projects'")
    print()
    
    # Simulate backend lookup
    print("Backend would find:")
    test_links = WorkItemAttachment.objects.filter(
        link_title='Projects',
        folder=root_folder,
        link_url__isnull=False
    )
    print(f"  {test_links.count()} links with title 'Projects' in folder {root_folder.id}")
    for link in test_links:
        print(f"    - ID: {link.id}, URL: {link.link_url}")
