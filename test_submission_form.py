"""
Test script to verify document type is saved in submission form.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from document_tracking.models import Submission, DocumentType
from document_tracking.forms import SubmissionForm

User = get_user_model()

# Get a regular user
user = User.objects.filter(is_staff=False).first()
if not user:
    print("❌ No regular user found")
    exit(1)

# Get a document type
doc_type = DocumentType.objects.filter(is_active=True).first()
if not doc_type:
    print("❌ No active document type found")
    print("Run: python manage.py create_default_document_types")
    exit(1)

print(f"✅ Testing with:")
print(f"   User: {user.username}")
print(f"   Document Type: {doc_type.name} ({doc_type.prefix})")

# Test 1: Form validation
print(f"\n📝 Test 1: Form Validation")
form_data = {
    'title': 'Test Submission',
    'purpose': 'Testing document type saving',
    'doc_type': doc_type.id,
}
form = SubmissionForm(data=form_data)
print(f"   Form valid: {form.is_valid()}")
if not form.is_valid():
    print(f"   Errors: {form.errors}")
    exit(1)

print(f"   Cleaned data doc_type: {form.cleaned_data.get('doc_type')}")

# Test 2: Form save
print(f"\n💾 Test 2: Form Save")
submission = form.save(commit=False)
submission.submitted_by = user
submission.status = 'pending_tracking'
print(f"   Submission doc_type before save: {submission.doc_type}")
submission.save()
print(f"   Submission doc_type after save: {submission.doc_type}")
print(f"   Submission ID: {submission.id}")

# Test 3: Verify from database
print(f"\n🔍 Test 3: Verify from Database")
submission_from_db = Submission.objects.get(id=submission.id)
print(f"   Doc type from DB: {submission_from_db.doc_type}")
print(f"   Doc type ID: {submission_from_db.doc_type.id if submission_from_db.doc_type else None}")

if submission_from_db.doc_type:
    print(f"\n✅ SUCCESS! Document type saved correctly: {submission_from_db.doc_type}")
else:
    print(f"\n❌ FAILED! Document type not saved")

# Test 4: Test via web client
print(f"\n🌐 Test 4: Test via Web Client")
client = Client()
client.force_login(user)

# Create a simple text file for upload
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

test_file = SimpleUploadedFile(
    "test.txt",
    b"Test file content",
    content_type="text/plain"
)

response = client.post(
    '/documents/submit/',
    data={
        'title': 'Web Test Submission',
        'purpose': 'Testing via web client',
        'doc_type': doc_type.id,
        'files': test_file,
    },
    follow=True
)

print(f"   Response status: {response.status_code}")

# Check if submission was created
latest_submission = Submission.objects.filter(submitted_by=user).order_by('-created_at').first()
if latest_submission:
    print(f"   Latest submission: #{latest_submission.id}")
    print(f"   Title: {latest_submission.title}")
    print(f"   Doc type: {latest_submission.doc_type}")
    
    if latest_submission.doc_type:
        print(f"\n✅ WEB TEST SUCCESS! Document type saved: {latest_submission.doc_type}")
    else:
        print(f"\n❌ WEB TEST FAILED! Document type not saved")
else:
    print(f"\n❌ No submission created")

# Cleanup
print(f"\n🧹 Cleanup: Deleting test submissions...")
Submission.objects.filter(title__in=['Test Submission', 'Web Test Submission']).delete()
print(f"   Done")
