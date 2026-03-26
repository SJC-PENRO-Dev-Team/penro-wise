"""
Check if the newly added links exist in the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder

# Get the KLEIN folder
klein_folder = DocumentFolder.objects.filter(name='KLEIN').first()

if klein_folder:
    print(f"KLEIN folder: ID {klein_folder.id}")
    print()
    
    # Get all links in KLEIN folder
    links = WorkItemAttachment.objects.filter(
        folder=klein_folder,
        link_url__isnull=False
    ).order_by('-uploaded_at')
    
    print(f"Total links in KLEIN: {links.count()}")
    print()
    
    # Show recent links
    print("Recent links (last 5):")
    for link in links[:5]:
        print(f"  ID: {link.id}")
        print(f"  Title: {link.link_title}")
        print(f"  URL: {link.link_url}")
        print(f"  Uploaded: {link.uploaded_at}")
        print(f"  Status: {link.acceptance_status}")
        print()
    
    # Check for "Sample" links
    sample_links = WorkItemAttachment.objects.filter(
        folder=klein_folder,
        link_title='Sample',
        link_url__isnull=False
    )
    
    print(f"Links with title 'Sample': {sample_links.count()}")
    for link in sample_links:
        print(f"  ID: {link.id}, URL: {link.link_url}")
else:
    print("KLEIN folder not found")
