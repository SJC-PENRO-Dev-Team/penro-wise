"""
Test the new permission denied page for tracking assignment.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from document_tracking.views import assign_tracking
from document_tracking.models import Submission

User = get_user_model()

# Create test request
factory = RequestFactory()

# Get a regular user (not admin)
user = User.objects.filter(is_staff=False, is_superuser=False).first()
if not user:
    print("❌ No regular user found")
    exit(1)

# Get a submission
submission = Submission.objects.first()
if not submission:
    print("❌ No submission found")
    exit(1)

print(f"✓ Testing with user: {user.email} (admin={user.is_staff})")
print(f"✓ Testing with submission ID: {submission.id}")

# Create POST request to assign tracking
request = factory.post(f'/documents/admin/submissions/{submission.id}/assign-tracking/')
request.user = user

# Call the view
response = assign_tracking(request, submission.id)

print(f"\n✓ Response status: {response.status_code}")
print(f"✓ Response type: {type(response).__name__}")

if response.status_code == 403:
    print("✓ Permission denied correctly (403)")
    
    # Check if it's rendering the template
    if hasattr(response, 'content'):
        content = response.content.decode('utf-8')
        if 'Access Denied' in content:
            print("✓ Styled error page rendered")
            if 'Admin Access Required' in content:
                print("✓ Error message present")
            if 'Return to Submission' in content or 'My Submissions' in content:
                print("✓ Return button present")
        else:
            print("❌ Plain text response (not styled)")
            print(f"Content preview: {content[:200]}")
else:
    print(f"❌ Unexpected status code: {response.status_code}")

print("\n✅ Test complete!")
