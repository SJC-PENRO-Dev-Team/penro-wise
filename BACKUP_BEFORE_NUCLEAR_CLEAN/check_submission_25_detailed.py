"""
Check submission #25 document type in detail.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission

try:
    submission = Submission.objects.select_related('doc_type').get(id=25)
    
    print("\n=== SUBMISSION #25 DETAILED CHECK ===")
    print(f"ID: {submission.id}")
    print(f"Title: {submission.title}")
    print(f"Status: {submission.status}")
    print(f"\n--- Document Type Field ---")
    print(f"doc_type (raw): {submission.doc_type}")
    print(f"doc_type type: {type(submission.doc_type)}")
    print(f"doc_type ID: {submission.doc_type.id if submission.doc_type else 'None'}")
    print(f"doc_type name: {submission.doc_type.name if submission.doc_type else 'None'}")
    print(f"doc_type prefix: {submission.doc_type.prefix if submission.doc_type else 'None'}")
    print(f"doc_type __str__: {str(submission.doc_type) if submission.doc_type else 'None'}")
    
    print(f"\n--- Template Display ---")
    print(f"{{ submission.doc_type }}: {submission.doc_type}")
    print(f"{{ submission.doc_type.name }}: {submission.doc_type.name if submission.doc_type else 'None'}")
    print(f"{{ submission.doc_type.prefix }}: {submission.doc_type.prefix if submission.doc_type else 'None'}")
    
    print("\n=== CHECK COMPLETE ===\n")
    
except Submission.DoesNotExist:
    print("\n✗ Submission #25 not found\n")
except Exception as e:
    print(f"\n✗ Error: {e}\n")
