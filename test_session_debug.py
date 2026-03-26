"""
Debug script to test session handling in tracking assignment.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from document_tracking.models import Submission

User = get_user_model()

# Get admin user
admin = User.objects.filter(is_staff=True, is_superuser=True).first()
if not admin:
    print("❌ No admin user found")
    exit(1)

# Get submission
submission = Submission.objects.filter(tracking_number__isnull=True).first()
if not submission:
    print("❌ No submission without tracking number found")
    exit(1)

print(f"✅ Testing with submission #{submission.id}")
print(f"   Admin user: {admin.username}")
print(f"   Doc type: {submission.doc_type}")

# Test with Django test client
client = Client()
client.force_login(admin)

# Step 1: Load the page
print("\n📄 Step 1: Loading submission detail page...")
response = client.get(f'/documents/admin/submissions/{submission.id}/')
print(f"   Status: {response.status_code}")

# Step 2: Submit preview
print("\n👁️  Step 2: Submitting preview...")
preview_data = {
    'action': 'preview',
    'document_type': submission.doc_type.id if submission.doc_type else 1,
    'assignment_mode': 'auto',
    'year': 2026,
}
response = client.post(
    f'/documents/admin/submissions/{submission.id}/assign-tracking/',
    data=preview_data,
    follow=True
)
print(f"   Status: {response.status_code}")

# Get messages
messages_list = list(get_messages(response.wsgi_request))
print(f"   Messages: {[str(m) for m in messages_list]}")

# Check session
session = client.session
print(f"\n🔍 Session data:")
print(f"   Session key exists: {bool(session.session_key)}")
tracking_preview = session.get('tracking_preview')
print(f"   tracking_preview exists: {tracking_preview is not None}")
if tracking_preview:
    print(f"   tracking_preview data: {tracking_preview}")

# Step 3: Submit confirm
print("\n🔒 Step 3: Submitting confirm...")
confirm_data = {
    'action': 'confirm',
}
response = client.post(
    f'/documents/admin/submissions/{submission.id}/assign-tracking/',
    data=confirm_data,
    follow=True
)
print(f"   Status: {response.status_code}")

# Get messages
messages_list = list(get_messages(response.wsgi_request))
print(f"   Messages: {[str(m) for m in messages_list]}")

# Check if tracking number was assigned
submission.refresh_from_db()
print(f"\n✅ Result:")
print(f"   Tracking number: {submission.tracking_number or 'Not assigned'}")
print(f"   Locked: {submission.tracking_locked}")

if submission.tracking_number:
    print(f"\n🎉 SUCCESS! Tracking number assigned: {submission.tracking_number}")
else:
    print(f"\n❌ FAILED! Tracking number not assigned")
