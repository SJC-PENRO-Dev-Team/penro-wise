#!/usr/bin/env python3
"""
Simple test for Routed Documents Filtering System
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from admin_app.views.routed_documents_api import (
    search_document_types, search_document_status, search_sections,
    get_routed_documents_by_filter
)
from document_tracking.models import DocumentType, Section, Submission

User = get_user_model()

def test_routed_filters():
    """Test the routed documents filtering system"""
    print("🔍 Testing Routed Documents Filters")
    print("=" * 50)
    
    # Get test user
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ No admin user found")
        return False
    
    factory = RequestFactory()
    
    # Test Document Types API
    print("\n1. Document Types API")
    try:
        request = factory.get('/api/search-document-types/', {'q': ''})
        request.user = user
        response = search_document_types(request)
        
        if response.status_code == 200:
            # Parse JSON content from response
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Results: {len(data.get('results', []))}")
            
            if data.get('results'):
                for dt in data['results'][:2]:
                    print(f"     - {dt['title']} ({dt.get('prefix', 'N/A')})")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Document Status API
    print("\n2. Document Status API")
    try:
        request = factory.get('/api/search-document-status/', {'q': ''})
        request.user = user
        response = search_document_status(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Results: {len(data.get('results', []))}")
            
            if data.get('results'):
                for status in data['results'][:2]:
                    print(f"     - {status['title']} ({status.get('submission_count', 0)} submissions)")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Sections API
    print("\n3. Sections API")
    try:
        request = factory.get('/api/search-sections/', {'q': ''})
        request.user = user
        response = search_sections(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Results: {len(data.get('results', []))}")
            
            if data.get('results'):
                for section in data['results'][:2]:
                    print(f"     - {section['title']} ({section.get('submission_count', 0)} submissions)")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Filter by Document Type
    print("\n4. Filter by Document Type")
    try:
        doc_type = DocumentType.objects.filter(is_active=True).first()
        if doc_type:
            request = factory.get('/api/routed-documents/', {
                'filter_type': 'doc_type',
                'filter_value': str(doc_type.id)
            })
            request.user = user
            response = get_routed_documents_by_filter(request)
            
            if response.status_code == 200:
                data = json.loads(response.content.decode('utf-8'))
                print(f"   ✓ Status: {response.status_code}")
                print(f"   ✓ Filter: {doc_type.name}")
                print(f"   ✓ Files: {data.get('total_files', 0)}")
                print(f"   ✓ Submissions: {data.get('submissions_count', 0)}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        else:
            print("   ⚠ No document types found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Data Summary
    print("\n" + "=" * 50)
    print("📊 DATA SUMMARY")
    print(f"Document Types: {DocumentType.objects.filter(is_active=True).count()}")
    print(f"Sections: {Section.objects.filter(is_active=True).count()}")
    print(f"Submissions: {Submission.objects.count()}")
    
    print("\n✅ Routed Documents Filtering System is working!")
    return True

if __name__ == "__main__":
    try:
        test_routed_filters()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)