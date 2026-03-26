"""
Test script to verify Document Tracking Settings page functionality.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import DocumentType, TrackingNumberSequence, Submission
from document_tracking.services.document_type_service import get_all_document_types, get_document_type_stats
from datetime import datetime

print("=" * 60)
print("DOCUMENT TRACKING SETTINGS - VERIFICATION TEST")
print("=" * 60)

# Test 1: Check Document Types
print("\n1. Document Types:")
print("-" * 60)
doc_types = get_all_document_types()
print(f"Total document types: {len(doc_types)}")
for dt in doc_types:
    print(f"  - {dt.name} ({dt.prefix}) - Order: {dt.order} - Active: {dt.is_active}")

# Test 2: Check Statistics
print("\n2. Document Type Statistics:")
print("-" * 60)
for dt in doc_types:
    stats = get_document_type_stats(dt.id)
    print(f"  {dt.name}:")
    print(f"    Total submissions: {stats['total_submissions']}")
    print(f"    This year: {stats['current_year_count']}")
    print(f"    Can delete: {stats['can_delete']}")

# Test 3: Check Tracking Sequences
print("\n3. Tracking Number Sequences:")
print("-" * 60)
current_year = datetime.now().year
sequences = TrackingNumberSequence.objects.filter(year=current_year).select_related('document_type')
print(f"Sequences for {current_year}: {sequences.count()}")
for seq in sequences:
    print(f"  - {seq.document_type.prefix}-{seq.year}-XXX (Last: {seq.last_serial})")

# Test 4: Check Submissions with Document Types
print("\n4. Submissions with Document Types:")
print("-" * 60)
total_submissions = Submission.objects.count()
with_doc_type = Submission.objects.filter(doc_type__isnull=False).count()
without_doc_type = Submission.objects.filter(doc_type__isnull=True).count()
print(f"Total submissions: {total_submissions}")
print(f"With document type: {with_doc_type}")
print(f"Without document type: {without_doc_type}")

# Test 5: URL Configuration
print("\n5. URL Configuration:")
print("-" * 60)
from django.urls import reverse
try:
    settings_url = reverse('document_tracking:settings')
    print(f"✓ Settings URL: {settings_url}")
    
    doc_types_url = reverse('document_tracking:document-types')
    print(f"✓ Document Types URL: {doc_types_url}")
    
    add_url = reverse('document_tracking:document-type-add')
    print(f"✓ Add Document Type URL: {add_url}")
    
    api_url = reverse('document_tracking:api-document-types')
    print(f"✓ API Document Types URL: {api_url}")
    
    print("\n✓ All Settings URLs configured correctly!")
except Exception as e:
    print(f"✗ URL configuration error: {e}")

# Test 6: Template Files
print("\n6. Template Files:")
print("-" * 60)
import os
template_dir = "templates/document_tracking/settings"
templates = [
    "index.html",
    "document_types.html",
    "document_type_form.html"
]
for template in templates:
    path = os.path.join(template_dir, template)
    exists = os.path.exists(path)
    status = "✓" if exists else "✗"
    print(f"{status} {template}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNext Steps:")
print("1. Start development server: python manage.py runserver")
print("2. Login as admin")
print("3. Navigate to Document Tracking → Settings")
print("4. Test all functionality:")
print("   - View settings dashboard")
print("   - List document types")
print("   - Add new document type")
print("   - Edit existing document type")
print("   - Drag-and-drop reorder")
print("   - Delete document type")
