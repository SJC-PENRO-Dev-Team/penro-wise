"""
Check submission #26 document type.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission

try:
    submission = Submission.objects.select_related('doc_type').get(id=26)
    
    print("\n=== SUBMISSION #26 CHECK ===")
    print(f"ID: {submission.id}")
    print(f"Title: {submission.title}")
    print(f"Status: {submission.status}")
    print(f"\n--- Document Type ---")
    print(f"doc_type: {submission.doc_type}")
    print(f"doc_type is None: {submission.doc_type is None}")
    if submission.doc_type:
        print(f"doc_type.id: {submission.doc_type.id}")
        print(f"doc_type.name: {submission.doc_type.name}")
        print(f"doc_type.prefix: {submission.doc_type.prefix}")
    
    print(f"\n--- OLD Field (deprecated) ---")
    print(f"document_type: {submission.document_type}")
    
    print("\n=== CHECK COMPLETE ===\n")
    
except Submission.DoesNotExist:
    print("\n✗ Submission #26 not found\n")
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()
