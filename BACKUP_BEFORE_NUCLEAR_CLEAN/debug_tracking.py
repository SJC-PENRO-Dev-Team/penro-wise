"""
Debug tracking assignment.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from accounts.models import User

# Get first submission
submission = Submission.objects.first()
user = User.objects.first()

print(f"Submission ID: {submission.id}")
print(f"Tracking Number: {submission.tracking_number}")
print(f"Tracking Locked: {submission.tracking_locked}")
print(f"Status: {submission.status}")
print(f"PK: {submission.pk}")

print("\n" + "=" * 60)
print("Attempting to assign tracking number...")
print("=" * 60)

# Try to assign manually
submission.tracking_number = "TEST-001"
submission.tracking_locked = True
submission.status = 'received'

print(f"\nBefore save:")
print(f"  tracking_number: {submission.tracking_number}")
print(f"  tracking_locked: {submission.tracking_locked}")
print(f"  status: {submission.status}")

try:
    submission.save()
    print("\n✓ Save successful!")
except Exception as e:
    print(f"\n❌ Save failed: {e}")
    import traceback
    traceback.print_exc()
