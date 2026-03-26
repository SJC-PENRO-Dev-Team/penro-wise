"""
Test script to verify tracking number assignment workflow.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType
from django.contrib.auth import get_user_model

User = get_user_model()

# Get a submission without tracking number
submission = Submission.objects.filter(tracking_number__isnull=True).first()

if not submission:
    print("❌ No submissions without tracking number found")
    print("Creating a test submission...")
    user = User.objects.filter(is_staff=False).first()
    if not user:
        print("❌ No regular user found")
        exit(1)
    
    # Create test submission
    from document_tracking.legacy_services import FileService
    submission = Submission.objects.create(
        title="Test Tracking Assignment",
        purpose="Testing the new tracking number assignment workflow",
        submitted_by=user,
        status='pending'
    )
    # Create primary folder
    FileService.create_primary_folder(submission)
    print(f"✅ Created test submission #{submission.id}")
else:
    print(f"✅ Found submission #{submission.id}: {submission.title}")

print(f"   Status: {submission.status}")
print(f"   Tracking Number: {submission.tracking_number or 'Not assigned'}")
print(f"   Document Type: {submission.doc_type or 'Not set'}")

# Check document types
doc_types = DocumentType.objects.filter(is_active=True)
print(f"\n📋 Active Document Types: {doc_types.count()}")
for dt in doc_types:
    print(f"   - {dt.name} ({dt.prefix})")

# Check if submission has doc_type
if not submission.doc_type:
    print(f"\n⚠️  Submission has no document type set!")
    print(f"   Setting to first active document type...")
    first_type = doc_types.first()
    if first_type:
        submission.doc_type = first_type
        submission.save()
        print(f"   ✅ Set to: {first_type.name} ({first_type.prefix})")
    else:
        print(f"   ❌ No active document types available!")
        print(f"   Run: python manage.py create_default_document_types")

print(f"\n🔗 Test URL:")
print(f"   http://127.0.0.1:8000/documents/admin/submissions/{submission.id}/")
print(f"\n📝 Steps to test:")
print(f"   1. Open the URL above")
print(f"   2. Scroll to 'Assign Serial Number' section")
print(f"   3. Select document type")
print(f"   4. Choose auto or manual mode")
print(f"   5. Click 'Preview' button")
print(f"   6. Check if preview message appears")
print(f"   7. Click 'Confirm & Lock' button")
print(f"   8. Verify tracking number is assigned")
