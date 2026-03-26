"""
Fix submissions that are missing document types.
Sets them to the default "General Document" type.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType

# Get default document type (General Document)
default_type = DocumentType.objects.filter(prefix='GEN').first()

if not default_type:
    print("❌ Default document type (GEN) not found")
    print("Run: python manage.py create_default_document_types")
    exit(1)

print(f"✅ Default document type: {default_type.name} ({default_type.prefix})")

# Find submissions without doc_type
submissions_without_type = Submission.objects.filter(doc_type__isnull=True)
count = submissions_without_type.count()

print(f"\n📊 Found {count} submissions without document type")

if count == 0:
    print("✅ All submissions have document types!")
    exit(0)

print(f"\n🔧 Updating submissions...")
for submission in submissions_without_type:
    print(f"   #{submission.id}: {submission.title}")
    submission.doc_type = default_type
    submission.save()

print(f"\n✅ Updated {count} submissions to use '{default_type.name}'")

# Verify
remaining = Submission.objects.filter(doc_type__isnull=True).count()
if remaining == 0:
    print(f"✅ All submissions now have document types!")
else:
    print(f"⚠️  {remaining} submissions still missing document type")
