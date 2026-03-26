"""
Test what the view is actually passing to the template for submission #26.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from document_tracking.views import submission_detail
from document_tracking.models import Submission

User = get_user_model()

try:
    # Get submission
    submission = Submission.objects.select_related('doc_type', 'assigned_section', 'submitted_by').get(id=26)
    
    print("\n=== SUBMISSION #26 DATA ===")
    print(f"ID: {submission.id}")
    print(f"Title: {submission.title}")
    print(f"doc_type object: {submission.doc_type}")
    print(f"doc_type is None: {submission.doc_type is None}")
    
    if submission.doc_type:
        print(f"doc_type.id: {submission.doc_type.id}")
        print(f"doc_type.name: {submission.doc_type.name}")
        print(f"doc_type.prefix: {submission.doc_type.prefix}")
        print(f"doc_type.__str__(): {str(submission.doc_type)}")
    
    # Test the view
    print("\n=== TESTING VIEW ===")
    factory = RequestFactory()
    request = factory.get(f'/documents/submission/{submission.id}/')
    request.user = submission.submitted_by
    
    # Call the view
    from document_tracking.views import submission_detail
    response = submission_detail(request, submission.id)
    
    print(f"Response status: {response.status_code}")
    print(f"Response has context: {hasattr(response, 'context_data')}")
    
    if hasattr(response, 'context_data'):
        context = response.context_data
        print(f"\nContext keys: {list(context.keys())}")
        
        if 'submission' in context:
            ctx_submission = context['submission']
            print(f"\nContext submission.doc_type: {ctx_submission.doc_type}")
            if ctx_submission.doc_type:
                print(f"Context submission.doc_type.name: {ctx_submission.doc_type.name}")
    
    print("\n=== TEST COMPLETE ===\n")
    
except Exception as e:
    print(f"\n✗ Error: {e}\n")
    import traceback
    traceback.print_exc()
