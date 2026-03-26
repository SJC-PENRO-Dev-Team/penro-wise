import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from collections import defaultdict

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
        print(f"  - uploaded_at: {att.uploaded_at}")
    
    # Test the grouping logic
    print("\n=== GROUPING LOGIC TEST ===")
    link_groups = {}
    single_links = []
    file_attachments = []
    
    temp_groups = defaultdict(list)
    
    for att in attachments:
        if att.link_url:
            if att.link_title:
                temp_groups[att.link_title].append(att)
            else:
                single_links.append(att)
        else:
            file_attachments.append(att)
    
    for title, links in temp_groups.items():
        if len(links) > 1:
            link_groups[title] = links
        else:
            single_links.extend(links)
    
    print(f"\nlink_groups: {link_groups}")
    print(f"single_links count: {len(single_links)}")
    print(f"file_attachments count: {len(file_attachments)}")
    
    if single_links:
        print("\nSingle links details:")
        for link in single_links:
            print(f"  - ID: {link.id}, Title: {link.link_title}, URL: {link.link_url}")
