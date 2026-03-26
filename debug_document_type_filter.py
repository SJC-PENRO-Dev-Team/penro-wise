#!/usr/bin/env python3
"""
Debug script to check document type filter issue
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

def debug_document_type_filter():
    print("=== DEBUGGING DOCUMENT TYPE FILTER ===\n")
    
    # Check document types
    print("1. Document Types in database:")
    doc_types = DocumentType.objects.all()
    print(f"Total document types: {doc_types.count()}")
    
    for dt in doc_types:
        submission_count = Submission.objects.filter(doc_type=dt).count()
        print(f"  - ID: {dt.id}, Name: {dt.name}, Prefix: {dt.prefix}, Active: {dt.is_active}, Submissions: {submission_count}")
    
    # Check submissions
    print(f"\n2. Total submissions: {Submission.objects.count()}")
    
    # Test the API endpoints
    client = Client()
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    print("\n3. Testing search_document_types API:")
    response = client.get('/admin/api/search-document-types/?q=')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"Results: {len(data.get('results', []))}")
        for result in data.get('results', []):
            print(f"  - ID: {result['id']}, Title: {result['title']}, Tracking: {result['tracking_number']}")
    else:
        print(f"Error: {response.content.decode('utf-8')}")
    
    # Test filtering by document type
    if doc_types.exists():
        first_doc_type = doc_types.first()
        print(f"\n4. Testing filter by document type ID {first_doc_type.id}:")
        
        response = client.get(f'/admin/api/routed-documents/?filter_type=doc_type&filter_value={first_doc_type.id}')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"Filter Status: {data.get('status')}")
            print(f"Total Files: {data.get('total_files')}")
            print(f"Filter Display: {data.get('filter_display')}")
        else:
            print(f"Error: {response.content.decode('utf-8')}")

if __name__ == "__main__":
    debug_document_type_filter()