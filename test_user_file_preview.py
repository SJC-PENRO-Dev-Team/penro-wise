"""
Test file preview functionality for user submission detail page.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from document_tracking.models import Submission
from accounts.models import WorkItemAttachment

User = get_user_model()

# Create test client
client = Client()

# Get a regular user (not admin)
user = User.objects.filter(is_staff=False, is_superuser=False).first()
if not user:
    print("❌ No regular user found")
    exit(1)

# Get a submission by this user with files
submission = Submission.objects.filter(submitted_by=user).first()
if not submission:
    print("❌ No submission found for user")
    exit(1)

print(f"✓ Testing with user: {user.email}")
print(f"✓ Testing with submission ID: {submission.id}")

# Get files from submission
files = []
if submission.primary_folder:
    files = list(submission.primary_folder.files.filter(link_url__isnull=True))
if submission.file_manager_folder:
    files.extend(list(submission.file_manager_folder.files.filter(link_url__isnull=True)))

if not files:
    print("❌ No files found in submission")
    exit(1)

test_file = files[0]
print(f"✓ Testing with file: {test_file.get_filename()} (ID: {test_file.id})")

# Login as user
client.force_login(user)

# Test 1: Access submission detail page
print("\n--- Test 1: Access Submission Detail Page ---")
response = client.get(f'/documents/submission/{submission.id}/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode('utf-8')
    
    # Check if FilePreview.show() is present
    if 'FilePreview.show' in content:
        print("✓ FilePreview.show() call found in template")
    else:
        print("❌ FilePreview.show() call NOT found")
    
    # Check if file preview modal is included
    if 'file_preview_modal.html' in content or 'filePreviewModal' in content:
        print("✓ File preview modal included")
    else:
        print("❌ File preview modal NOT included")
    
    # Check if file is listed
    if test_file.get_filename() in content:
        print(f"✓ File '{test_file.get_filename()}' is listed")
    else:
        print(f"❌ File '{test_file.get_filename()}' NOT listed")
else:
    print(f"❌ Failed to access page: {response.status_code}")

# Test 2: Access file info endpoint
print("\n--- Test 2: Access File Info Endpoint ---")
response = client.get(f'/user/documents/files/info/{test_file.id}/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✓ File info endpoint accessible")
    try:
        data = response.json()
        print(f"✓ File name: {data.get('name')}")
        print(f"✓ File type: {data.get('type')}")
        print(f"✓ File size: {data.get('size')} bytes")
        print(f"✓ Download URL: {data.get('download_url')}")
    except Exception as e:
        print(f"❌ Failed to parse JSON: {e}")
else:
    print(f"❌ Failed to access endpoint: {response.status_code}")

# Test 3: Check URL detection logic
print("\n--- Test 3: URL Detection Logic ---")
test_urls = [
    '/documents/submission/19/',
    '/documents/submit/',
    '/documents/my-submissions/',
    '/user/workitems/',
    '/admin/documents/files/',
]

for url in test_urls:
    # Simulate the JavaScript logic
    is_user = (url.startswith('/user/') or 
               url.startswith('/documents/submission/') or
               bool(__import__('re').match(r'^/documents/(submit|my-submissions)', url)))
    prefix = '/user' if is_user else '/admin'
    print(f"URL: {url:40} → Prefix: {prefix}")

print("\n✅ All tests complete!")
