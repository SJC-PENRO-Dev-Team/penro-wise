"""
Check all recently added links
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from django.utils import timezone
from datetime import timedelta

# Get links added in the last 10 minutes
recent_time = timezone.now() - timedelta(minutes=10)

recent_links = WorkItemAttachment.objects.filter(
    link_url__isnull=False,
    uploaded_at__gte=recent_time
).order_by('-uploaded_at')

print(f"Links added in the last 10 minutes: {recent_links.count()}")
print()

for link in recent_links:
    print(f"ID: {link.id}")
    print(f"Title: {link.link_title}")
    print(f"URL: {link.link_url}")
    print(f"Folder: {link.folder.name if link.folder else 'None'}")
    print(f"Folder ID: {link.folder_id}")
    print(f"Status: {link.acceptance_status}")
    print(f"Uploaded: {link.uploaded_at}")
    print()
