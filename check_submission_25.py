"""
Check submission #25 document type.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission

try:
    submission = Submission.objects.get(id=25)
    print(f"✅ Submission #25 found")
    print(f"   Title: {submission.title}")
    print(f"   Doc Type: {submission.doc_type}")
    print(f"   Doc Type ID: {submission.doc_type.id if submission.doc_type else None}")
    print(f"   Doc Type Prefix: {submission.doc_type.prefix if submission.doc_type else None}")
    print(f"   Status: {submission.status}")
    print(f"   Submitted by: {submission.submitted_by}")
    print(f"   Created at: {submission.created_at}")
    
    # Check the raw database value
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT doc_type_id FROM document_tracking_submission WHERE id = 25")
        row = cursor.fetchone()
        print(f"\n   Raw doc_type_id from DB: {row[0] if row else 'Not found'}")
    
except Submission.DoesNotExist:
    print("❌ Submission #25 not found")
