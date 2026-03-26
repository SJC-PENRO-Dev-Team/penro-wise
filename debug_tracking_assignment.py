"""
Debug tracking assignment issue.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType

# Check submission 26
try:
    submission = Submission.objects.select_related('doc_type').get(id=26)
    
    print("\n=== SUBMISSION #26 ===")
    print(f"ID: {submission.id}")
    print(f"Title: {submission.title}")
    print(f"doc_type: {submission.doc_type}")
    print(f"doc_type ID: {submission.doc_type.id if submission.doc_type else 'None'}")
    
    print("\n=== AVAILABLE DOCUMENT TYPES ===")
    doc_types = DocumentType.objects.filter(is_active=True)
    for dt in doc_types:
        print(f"  - ID: {dt.id}, Name: {dt.name}, Prefix: {dt.prefix}, Active: {dt.is_active}")
    
    print("\n=== TEST COMPLETE ===\n")
    
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()
