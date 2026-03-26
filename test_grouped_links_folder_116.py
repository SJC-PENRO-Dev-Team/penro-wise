"""
Test grouped links endpoint with folder 116.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from document_tracking.models import Submission
from structure.models import DocumentFolder

# Get submission 19
submission = Submission.objects.get(id=19)
user = submission.submitted_by

print(f"User: {user.email}")
print(f"Submission: {submission.id}")

# Check folder 116
try:
    folder = DocumentFolder.objects.get(id=116)
    print(f"\n✓ Folder 116 exists")
    print(f"  Type: {folder.folder_type}")
    print(f"  Name: {folder.name}")
    
    # Check links in folder
    from accounts.models import WorkItemAttachment
    links = WorkItemAttachment.objects.filter(
        folder=folder,
        link_title='fucking ehll',
        link_url__isnull=False
    )
    print(f"  Links with title 'fucking ehll': {links.count()}")
    for link in links:
        print(f"    - {link.link_url}")
except DocumentFolder.DoesNotExist:
    print("❌ Folder 116 does not exist")

# Test endpoint
client = Client()
client.force_login(user)

print(f"\n--- Testing Endpoint ---")
url = f'/user/documents/files/grouped-links/116/fucking%20ehll/'
print(f"URL: {url}")

response = client.get(url)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"✓ Success!")
        print(f"  Links: {data.get('count', 0)}")
        for link in data.get('links', []):
            print(f"    - {link.get('url')}")
    except:
        print(f"❌ Not JSON")
        print(f"Content: {response.content[:300]}")
else:
    print(f"❌ Failed")
    print(f"Content: {response.content[:500]}")
