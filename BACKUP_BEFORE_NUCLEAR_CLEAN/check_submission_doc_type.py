"""
Diagnostic script to check submission document type issue.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType

print("=" * 60)
print("CHECKING SUBMISSION DOCUMENT TYPE ISSUE")
print("=" * 60)

# Get the submission that's causing issues
submission_id = input("\nEnter submission ID (or press Enter for latest): ").strip()

if submission_id:
    try:
        submission = Submission.objects.get(id=int(submission_id))
    except Submission.DoesNotExist:
        print(f"❌ Submission #{submission_id} not found")
        exit(1)
else:
    submission = Submission.objects.order_by('-id').first()
    if not submission:
        print("❌ No submissions found in database")
        exit(1)

print(f"\n📋 SUBMISSION #{submission.id}")
print(f"   Title: {submission.title}")
print(f"   Status: {submission.status}")
print(f"   Tracking Number: {submission.tracking_number or 'NOT ASSIGNED'}")
print(f"   Tracking Locked: {submission.tracking_locked}")

print(f"\n📄 DOCUMENT TYPE INFO:")
print(f"   doc_type (FK): {submission.doc_type}")
if submission.doc_type:
    print(f"   doc_type.id: {submission.doc_type.id}")
    print(f"   doc_type.name: {submission.doc_type.name}")
    print(f"   doc_type.prefix: {submission.doc_type.prefix}")
    print(f"   doc_type.serial_mode: {submission.doc_type.serial_mode}")
else:
    print("   ⚠️  doc_type is NULL!")

print(f"\n   document_type (old field): {submission.document_type}")

print(f"\n🔍 DIAGNOSIS:")

if submission.tracking_number:
    print(f"   ⚠️  Submission ALREADY has tracking number: {submission.tracking_number}")
    print(f"   ℹ️  This is why you're getting 'Invalid document type' error")
    print(f"   ℹ️  The system prevents re-assigning tracking numbers")
    
    if submission.tracking_locked:
        print(f"   🔒 Tracking number is LOCKED")
        print(f"   ℹ️  Cannot be changed once locked")
    else:
        print(f"   🔓 Tracking number is NOT locked")
        print(f"   ℹ️  Could potentially be reassigned")
    
    print(f"\n💡 SOLUTION:")
    print(f"   Option 1: Create a NEW submission to test tracking assignment")
    print(f"   Option 2: Manually clear tracking number (for testing only):")
    print(f"   ")
    print(f"   python manage.py shell")
    print(f"   >>> from document_tracking.models import Submission")
    print(f"   >>> s = Submission.objects.get(id={submission.id})")
    print(f"   >>> s.tracking_number = None")
    print(f"   >>> s.tracking_locked = False")
    print(f"   >>> s.save()")
    print(f"   >>> exit()")

elif not submission.doc_type:
    print(f"   ❌ doc_type is NULL - submission has no document type assigned")
    print(f"   ℹ️  This should have been set during submission creation")
    
    print(f"\n💡 SOLUTION:")
    print(f"   Assign a document type to this submission:")
    print(f"   ")
    print(f"   python manage.py shell")
    print(f"   >>> from document_tracking.models import Submission, DocumentType")
    print(f"   >>> s = Submission.objects.get(id={submission.id})")
    print(f"   >>> dt = DocumentType.objects.first()  # or get specific one")
    print(f"   >>> s.doc_type = dt")
    print(f"   >>> s.save()")
    print(f"   >>> exit()")

else:
    print(f"   ✅ Submission looks good - ready for tracking assignment")
    print(f"   ℹ️  doc_type is set: {submission.doc_type.name}")
    print(f"   ℹ️  No tracking number assigned yet")

print("\n" + "=" * 60)

# Show all document types
print("\n📚 AVAILABLE DOCUMENT TYPES:")
doc_types = DocumentType.objects.all()
if doc_types:
    for dt in doc_types:
        print(f"   • {dt.name} ({dt.prefix}) - Mode: {dt.serial_mode}")
else:
    print("   ⚠️  No document types found!")
    print("   Run: python manage.py create_default_document_types")

print("\n" + "=" * 60)
