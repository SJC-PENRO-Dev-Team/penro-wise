import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from document_tracking.views import submission_detail
from document_tracking.models import Submission

User = get_user_model()

# Get submission 18
submission = Submission.objects.get(id=18)
print(f"Submission: {submission.title}")
print(f"Submitted by: {submission.submitted_by}")

# Create a request
factory = RequestFactory()
request = factory.get(f'/documents/submission/18/')
request.user = submission.submitted_by

# Call the view
response = submission_detail(request, 18)

print(f"\nResponse status: {response.status_code}")

# Check context
from django.template.response import TemplateResponse
if isinstance(response, TemplateResponse):
    context = response.context_data
else:
    print("Response is not a TemplateResponse, rendering to get context...")
    # The view uses render() which returns HttpResponse, not TemplateResponse
    # We need to check the actual rendered content
    print("Cannot access context directly from HttpResponse")
    print("\nLet's check the database directly instead:")
    from collections import defaultdict
    
    link_groups = {}
    single_links = []
    file_attachments = []
    
    if submission.primary_folder:
        temp_groups = defaultdict(list)
        
        for att in submission.primary_folder.files.all():
            if att.link_url:
                if att.link_title:
                    temp_groups[att.link_title].append(att)
                else:
                    single_links.append(att)
            else:
                file_attachments.append(att)
        
        for title, links in temp_groups.items():
            if len(links) > 1:
                link_groups[title] = links
            else:
                single_links.extend(links)
    
    context = {
        'link_groups': link_groups,
        'single_links': single_links,
        'file_attachments': file_attachments,
    }
print(f"\nContext keys: {list(context.keys())}")
print(f"link_groups: {context.get('link_groups')}")
print(f"single_links count: {len(context.get('single_links', []))}")
print(f"file_attachments count: {len(context.get('file_attachments', []))}")

if context.get('single_links'):
    for link in context['single_links']:
        print(f"\nSingle link:")
        print(f"  ID: {link.id}")
        print(f"  Title: {link.link_title}")
        print(f"  URL: {link.link_url}")
