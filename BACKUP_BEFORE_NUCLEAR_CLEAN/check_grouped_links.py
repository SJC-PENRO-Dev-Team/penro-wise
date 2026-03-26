import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment

# Find all links
links = WorkItemAttachment.objects.filter(
    link_url__isnull=False
).order_by('work_item_id', 'link_title', 'uploaded_at')

print(f"\n=== ALL LINKS IN DATABASE ===")
print(f"Total links: {links.count()}\n")

if links.exists():
    current_work_item = None
    current_title = None
    
    for link in links:
        if current_work_item != link.work_item_id:
            current_work_item = link.work_item_id
            print(f"\n--- Work Item #{link.work_item_id} ---")
        
        if current_title != link.link_title:
            current_title = link.link_title
            count = links.filter(work_item_id=link.work_item_id, link_title=link.link_title).count()
            print(f"\nGroup: '{link.link_title}' ({count} link{'s' if count > 1 else ''})")
        
        print(f"  - ID: {link.id}")
        print(f"    URL: {link.link_url[:60]}...")
        print(f"    Type: {link.attachment_type}")
        print(f"    Status: {link.acceptance_status}")
        print(f"    Uploaded: {link.uploaded_at.strftime('%Y-%m-%d %H:%M')}")
else:
    print("No links found in database")
