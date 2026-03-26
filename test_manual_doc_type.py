#!/usr/bin/env python3
"""
Test script to check manual document type filter
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from document_tracking.models import DocumentType, Submission

def test_manual_doc_type():
    print("=== TESTING MANUAL DOCUMENT TYPE FILTER ===\n")
    
    # Get the MANUAL INPUT document type
    manual_doc_type = DocumentType.objects.get(name="MANUAL INPUT")
    print(f"Testing with Document Type: {manual_doc_type.name} (ID: {manual_doc_type.id})")
    
    # Check submissions for this doc type
    submissions = Submission.objects.filter(doc_type=manual_doc_type)
    print(f"Submissions for this doc type: {submissions.count()}")
    
    for submission in submissions:
        print(f"  - ID: {submission.id}, Title: {submission.title}, Status: {submission.status}")
        print(f"    Primary Folder: {submission.primary_folder_id}")
        print(f"    Archive Folder: {submission.archive_folder_id}")
        print(f"    File Manager Folder: {submission.file_manager_folder_id}")
    
    # Test the API
    client = Client()
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    print(f"\nTesting filter by document type ID {manual_doc_type.id}:")
    response = client.get(f'/admin/api/routed-documents/?filter_type=doc_type&filter_value={manual_doc_type.id}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"Filter Status: {data.get('status')}")
        print(f"Total Files: {data.get('total_files')}")
        print(f"Filter Display: {data.get('filter_display')}")
        print(f"Submissions Count: {data.get('submissions_count')}")
        
        # Check if HTML contains files
        html = data.get('html', '')
        if 'fm-item' in html:
            print("✓ HTML contains file items")
        else:
            print("✗ HTML does not contain file items")
            
        if 'No routed documents found' in html:
            print("✗ Shows 'No routed documents found'")
        else:
            print("✓ Does not show 'No routed documents found'")
    else:
        print(f"Error: {response.content.decode('utf-8')}")

if __name__ == "__main__":
    test_manual_doc_type()