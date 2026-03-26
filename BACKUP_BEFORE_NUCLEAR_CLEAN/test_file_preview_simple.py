"""
Simple test for file preview on user submission page.
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

print(f"✓ User: {user.email} (admin={user.is_staff})")
print(f"✓ Submission: {submission.id} - {submission.title}")

# Get files
files = []
if submission.primary_folder:
    files = list(submission.primary_folder.files.filter(link_url__isnull=True))
if submission.file_manager_folder:
    files.extend(list(submission.file_manager_folder.files.filter(link_url__isnull=True)))

print(f"✓ Files found: {len(files)}")
for f in files:
    print(f"  - {f.get_filename()} (ID: {f.id})")

# Test with client
client = Client()
client.force_login(user)

# Test submission detail page
print("\n--- Testing Submission Detail Page ---")
response = client.get(f'/documents/submission/{submission.id}/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    
    # Check for FilePreview
    has_file_preview = 'FilePreview.show' in content
    has_modal = 'filePreviewModal' in content
    
    print(f"FilePreview.show() present: {has_file_preview}")
    print(f"File preview modal present: {has_modal}")
    
    if files:
        test_file = files[0]
        print(f"\n--- Testing File Info Endpoint ---")
        response2 = client.get(f'/user/documents/files/info/{test_file.id}/')
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data = response2.json()
            print(f"✓ File info retrieved:")
            print(f"  Name: {data.get('name')}")
            print(f"  Type: {data.get('type')}")
            print(f"  URL: {data.get('url')}")
        else:
            print(f"❌ Failed: {response2.status_code}")

print("\n✅ Test complete!")
