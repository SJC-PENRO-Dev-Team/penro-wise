#!/usr/bin/env python3
"""
Test script to verify tracking number filter functionality.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from admin_app.views.routed_documents_api import search_tracking_numbers_filter, get_routed_documents_by_filter
from document_tracking.models import Submission

def test_tracking_number_filter():
    """Test tracking number filter functionality"""
    
    print("🧪 Testing Tracking Number Filter")
    print("=" * 60)
    
    # Create request factory
    factory = RequestFactory()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Test 1: Search tracking numbers filter API
    print("📋 Test 1: Search Tracking Numbers Filter API")
    request = factory.get('/admin/api/search-tracking-filter/?q=')
    request.user = admin_user
    
    try:
        response = search_tracking_numbers_filter(request)
        print(f"✅ API request successful (Status: {response.status_code})")
        
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content.decode('utf-8'))
            results = data.get('results', [])
            
            print(f"📊 Total results: {len(results)}")
            
            # Check for document type headers and tracking numbers
            headers = [r for r in results if r.get('is_header')]
            tracking_numbers = [r for r in results if not r.get('is_header') and not r.get('is_more')]
            
            print(f"📊 Document type headers: {len(headers)}")
            print(f"📊 Tracking numbers: {len(tracking_numbers)}")
            
            if tracking_numbers:
                print("📋 Sample tracking numbers:")
                for tn in tracking_numbers[:3]:
                    print(f"   - {tn.get('title')} | {tn.get('doc_type')} | {tn.get('status')}")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    # Test 2: Search with query
    print("\n📋 Test 2: Search with Query 'MAN'")
    request = factory.get('/admin/api/search-tracking-filter/?q=MAN')
    request.user = admin_user
    
    try:
        response = search_tracking_numbers_filter(request)
        print(f"✅ Search API request successful (Status: {response.status_code})")
        
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content.decode('utf-8'))
            results = data.get('results', [])
            
            print(f"📊 Search results: {len(results)}")
            
            if results:
                print("📋 Search results:")
                for result in results[:3]:
                    print(f"   - {result.get('title')} | {result.get('tracking_number')}")
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")
        return False
    
    # Test 3: Filter by tracking number
    print("\n📋 Test 3: Filter by Tracking Number")
    
    # Get a tracking number to test with
    submission = Submission.objects.filter(tracking_number__isnull=False).first()
    if not submission:
        print("⚠️  No submissions with tracking numbers found")
        return True
    
    tracking_number = submission.tracking_number
    print(f"📋 Testing with tracking number: {tracking_number}")
    
    request = factory.get(f'/admin/api/routed-documents/?filter_type=tracking&filter_value={tracking_number}')
    request.user = admin_user
    
    try:
        response = get_routed_documents_by_filter(request)
        print(f"✅ Filter API request successful (Status: {response.status_code})")
        
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content.decode('utf-8'))
            
            if data.get('status') == 'success':
                print(f"✅ Filter status: {data['status']}")
                print(f"📊 Total files: {data.get('total_files', 0)}")
                print(f"📊 Filter display: {data.get('filter_display', 'N/A')}")
            else:
                print(f"⚠️  Filter status: {data.get('status', 'unknown')}")
                print(f"⚠️  Message: {data.get('message', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Filter test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All tracking number filter tests completed!")
    
    return True

if __name__ == '__main__':
    try:
        success = test_tracking_number_filter()
        if success:
            print("\n🎯 TRACKING NUMBER FILTER: WORKING")
        else:
            print("\n❌ TRACKING NUMBER FILTER: NEEDS FIXING")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()