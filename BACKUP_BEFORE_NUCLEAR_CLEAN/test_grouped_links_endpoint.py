"""
Test grouped links endpoint for users.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from document_tracking.models import Submission

# Get submission 19
submission = Submission.objects.get(id=19)
user = submission.submitted_by

print(f"Testing grouped links endpoint for user: {user.email}")
print(f"Submission: {submission.id}")
print(f"Primary folder: {submission.primary_folder.id if submission.primary_folder else 'None'}")

# Test with client
client = Client()
client.force_login(user)

# Test the endpoint
group_name = "fucking ehll"
folder_id = submission.primary_folder.id

print(f"\n--- Testing User Endpoint ---")
url = f'/user/documents/files/grouped-links/{folder_id}/{group_name}/'
print(f"URL: {url}")

response = client.get(url)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'N/A')}")

if response.status_code == 200:
    try:
        data = response.json()
        print(f"✓ JSON response received")
        print(f"  Links count: {len(data.get('links', []))}")
        for i, link in enumerate(data.get('links', [])[:3], 1):
            print(f"  Link {i}: {link.get('url', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"Content preview: {response.content[:200]}")
else:
    print(f"❌ Failed with status {response.status_code}")
    print(f"Content preview: {response.content[:500]}")

print("\n✅ Test complete!")
