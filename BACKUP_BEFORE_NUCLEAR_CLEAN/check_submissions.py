"""
Check submission tracking status.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission

print("=" * 60)
print("CHECKING ALL SUBMISSIONS")
print("=" * 60)

submissions = Submission.objects.all().order_by('id')

for sub in submissions:
    print(f"\nID: {sub.id}")
    print(f"  Title: {sub.title}")
    print(f"  Tracking Number: {sub.tracking_number}")
    print(f"  Tracking Locked: {sub.tracking_locked}")
    print(f"  Status: {sub.status}")
    print(f"  Is Locked: {sub.is_locked}")
    print(f"  Created: {sub.created_at}")

print(f"\n\nTotal submissions: {submissions.count()}")
print(f"With tracking numbers: {submissions.filter(tracking_number__isnull=False).count()}")
print(f"Without tracking numbers: {submissions.filter(tracking_number__isnull=True).count()}")
print(f"Tracking locked: {submissions.filter(tracking_locked=True).count()}")
