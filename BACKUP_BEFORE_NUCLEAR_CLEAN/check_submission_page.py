#!/usr/bin/env python
"""
Check if submission detail page is working correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
django.setup()

from document_tracking.models import Submission
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("CHECKING SUBMISSION DETAIL PAGE")
print("=" * 80)

# Check if submission 12 exists
try:
    submission = Submission.objects.get(id=12)
    print(f"\n✓ Submission #{submission.id} exists")
    print(f"  Title: {submission.title}")
    print(f"  Status: {submission.status}")
    print(f"  Submitted by: {submission.submitted_by.get_full_name()}")
    print(f"  Tracking number: {submission.tracking_number or 'Not assigned'}")
    
    # Check primary folder
    if submission.primary_folder:
        print(f"\n✓ Primary folder exists (ID: {submission.primary_folder.id})")
        files_count = submission.primary_folder.files.count()
        print(f"  Files/Links: {files_count}")
        
        if files_count > 0:
            for attachment in submission.primary_folder.files.all()[:5]:
                if attachment.link_url:
                    print(f"    - Link: {attachment.link_title or 'Untitled'}")
                else:
                    print(f"    - File: {attachment.get_filename()}")
    else:
        print("\n✗ No primary folder")
    
    # Check logbook entries
    logs_count = submission.logs.count()
    print(f"\n✓ Activity log entries: {logs_count}")
    
    print("\n" + "=" * 80)
    print("TEMPLATE CHECK")
    print("=" * 80)
    
    # Check template file
    template_path = 'templates/document_tracking/submission_detail.html'
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n✓ Template exists: {template_path}")
        print(f"  Size: {len(content)} characters")
        print(f"  Lines: {content.count(chr(10)) + 1}")
        
        # Check for critical elements
        checks = {
            'Extends admin base': '{% extends "admin/layout/base.html" %}' in content,
            'Has content block': '{% block content %}' in content,
            'Loads static': '{% load static %}' in content,
            'Has CSS link': 'document-tracking.css' in content,
            'Has back button': 'Back to My Submissions' in content,
            'Has modals': 'singleLinkModal' in content,
            'Has JavaScript': 'showSingleLinkModal' in content,
        }
        
        print("\n  Critical elements:")
        all_ok = True
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"    {status} {check}")
            if not passed:
                all_ok = False
        
        if not all_ok:
            print("\n  ✗ Template has missing elements!")
        else:
            print("\n  ✓ Template looks good!")
            
    else:
        print(f"\n✗ Template not found: {template_path}")
    
except Submission.DoesNotExist:
    print("\n✗ Submission #12 does not exist")
    print("\nAvailable submissions:")
    for sub in Submission.objects.all()[:10]:
        print(f"  - ID {sub.id}: {sub.title} (by {sub.submitted_by.get_full_name()})")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TROUBLESHOOTING STEPS")
print("=" * 80)
print("""
If the page is blank:

1. Check browser console (F12) for JavaScript errors
2. Check Django server console for template errors
3. Try hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
4. Check if you're logged in as the correct user
5. Verify the URL is correct: /documents/submission/12/
6. Check Django logs for any errors
7. Try accessing a different submission ID
""")
print("=" * 80)
