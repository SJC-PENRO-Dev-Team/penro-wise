#!/usr/bin/env python3
"""
Test script to verify the document type filter fix for "Invalid filter type" error
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

def test_document_type_filter_final():
    print("=== TESTING DOCUMENT TYPE FILTER - FINAL FIX ===\n")
    
    client = Client()
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    # Test the specific issue: filter_type with underscore vs hyphen
    print("1. Testing filter_type parameter formats:")
    
    # Test with hyphen (old, should fail)
    print("   a) Testing with hyphen (doc-type) - should fail:")
    response = client.get('/admin/api/routed-documents/?filter_type=doc-type&filter_value=2')
    print(f"      Status: {response.status_code}")
    if response.status_code == 400:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"      Message: {data.get('message')}")
        if data.get('message') == 'Invalid filter type':
            print("      ✓ Correctly rejects hyphenated filter type")
    
    # Test with underscore (new, should work)
    print("   b) Testing with underscore (doc_type) - should work:")
    response = client.get('/admin/api/routed-documents/?filter_type=doc_type&filter_value=2')
    print(f"      Status: {response.status_code}")
    if response.status_code == 200:
        import json
        data = json.loads(response.content.decode('utf-8'))
        print(f"      Status: {data.get('status')}")
        print(f"      Filter Display: {data.get('filter_display')}")
        print(f"      Total Files: {data.get('total_files')}")
        print("      ✓ Successfully processes underscore filter type")
    
    # Test all valid filter types
    print("\n2. Testing all valid filter types:")
    valid_types = ['doc_type', 'status', 'section', 'tracking']
    
    for filter_type in valid_types:
        print(f"   Testing {filter_type}:")
        
        if filter_type == 'doc_type':
            # Use a valid document type ID
            doc_type = DocumentType.objects.first()
            filter_value = doc_type.id
        elif filter_type == 'status':
            # Use a valid status
            filter_value = 'approved'
        elif filter_type == 'section':
            # Skip section test if no sections exist
            from document_tracking.models import Section
            if not Section.objects.exists():
                print(f"      Skipped - no sections exist")
                continue
            section = Section.objects.first()
            filter_value = section.id
        elif filter_type == 'tracking':
            # Use a valid tracking number
            submission = Submission.objects.filter(tracking_number__isnull=False).first()
            if not submission:
                print(f"      Skipped - no tracking numbers exist")
                continue
            filter_value = submission.tracking_number
        
        response = client.get(f'/admin/api/routed-documents/?filter_type={filter_type}&filter_value={filter_value}')
        print(f"      Status: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"      Result: {data.get('status')} - {data.get('filter_display')}")
        else:
            print(f"      Error: {response.content.decode('utf-8')[:100]}...")
    
    print("\n3. Testing invalid filter types:")
    invalid_types = ['doc-type', 'invalid', 'document_type', 'doc_types']
    
    for filter_type in invalid_types:
        response = client.get(f'/admin/api/routed-documents/?filter_type={filter_type}&filter_value=1')
        if response.status_code == 400:
            data = json.loads(response.content.decode('utf-8'))
            if data.get('message') == 'Invalid filter type':
                print(f"   ✓ {filter_type} correctly rejected")
        else:
            print(f"   ✗ {filter_type} should be rejected but got status {response.status_code}")

if __name__ == "__main__":
    test_document_type_filter_final()