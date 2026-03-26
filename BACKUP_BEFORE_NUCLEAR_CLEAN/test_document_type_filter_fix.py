#!/usr/bin/env python3
"""
Test script to verify document type filter fixes
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

def test_document_type_filter_fix():
    print("=== TESTING DOCUMENT TYPE FILTER FIXES ===\n")
    
    client = Client()
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    # Test 1: Load document types API
    print("1. Testing document types API:")
    response = client.get('/admin/api/search-document-types/?q=')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"Document types returned: {len(data.get('results', []))}")
        for result in data.get('results', []):
            print(f"  - {result['title']} ({result['prefix']}) - {result['submission_count']} submissions")
    
    # Test 2: Filter by document type with files (MANUAL INPUT)
    manual_doc_type = DocumentType.objects.get(name="MANUAL INPUT")
    print(f"\n2. Testing filter by {manual_doc_type.name} (should have files):")
    
    response = client.get(f'/admin/api/routed-documents/?filter_type=doc_type&filter_value={manual_doc_type.id}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        print(f"Filter Status: {data.get('status')}")
        print(f"Total Files: {data.get('total_files')}")
        print(f"Submissions Count: {data.get('submissions_count')}")
        print(f"Filter Display: {data.get('filter_display')}")
        
        html = data.get('html', '')
        if 'No documents found' in html:
            print("✗ Shows 'No documents found' (should show files)")
        else:
            print("✓ Does not show 'No documents found'")
    
    # Test 3: Filter by document type with no files (Automatic)
    auto_doc_type = DocumentType.objects.get(name="Automatic")
    print(f"\n3. Testing filter by {auto_doc_type.name} (should have no files):")
    
    response = client.get(f'/admin/api/routed-documents/?filter_type=doc_type&filter_value={auto_doc_type.id}')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = json.loads(response.content.decode('utf-8'))
        print(f"Filter Status: {data.get('status')}")
        print(f"Total Files: {data.get('total_files')}")
        print(f"Submissions Count: {data.get('submissions_count')}")
        print(f"Filter Display: {data.get('filter_display')}")
        
        html = data.get('html', '')
        if 'No documents found' in html:
            print("✓ Shows 'No documents found' (correct for empty filter)")
        else:
            print("✗ Does not show 'No documents found' (should show empty message)")
    
    # Test 4: Test invalid filter value
    print(f"\n4. Testing invalid filter value:")
    response = client.get(f'/admin/api/routed-documents/?filter_type=doc_type&filter_value=999')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("✓ Returns 404 for invalid document type ID")
    else:
        print(f"✗ Expected 404, got {response.status_code}")

if __name__ == "__main__":
    test_document_type_filter_fix()