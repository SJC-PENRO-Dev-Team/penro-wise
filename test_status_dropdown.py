#!/usr/bin/env python3
"""
Test script for Status Dropdown Functionality
Tests the new dropdown select with submission counts
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
from admin_app.views.routed_documents_api import search_document_status
from document_tracking.models import Submission

User = get_user_model()

def test_status_dropdown():
    """Test the status dropdown functionality"""
    print("🔍 Testing Status Dropdown")
    print("=" * 40)
    
    # Get test user
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ No admin user found")
        return False
    
    factory = RequestFactory()
    
    # Test 1: Load all statuses (no query)
    print("\n1. Loading All Statuses (Dropdown)")
    try:
        request = factory.get('/api/search-document-status/', {'q': ''})
        request.user = user
        response = search_document_status(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Total statuses: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("   📊 Status breakdown:")
                for status in data['results']:
                    print(f"     - {status['title']}: {status['submission_count']} submissions")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Search specific status
    print("\n2. Search Specific Status")
    try:
        request = factory.get('/api/search-document-status/', {'q': 'approved'})
        request.user = user
        response = search_document_status(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Filtered results: {len(data.get('results', []))}")
            
            if data.get('results'):
                for status in data['results']:
                    print(f"     - {status['title']}: {status['submission_count']} submissions")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check submission data
    print("\n3. Database Status Distribution")
    try:
        total_submissions = Submission.objects.count()
        print(f"   📈 Total submissions: {total_submissions}")
        
        for status_code, status_display in Submission.STATUS_CHOICES:
            count = Submission.objects.filter(status=status_code).count()
            if count > 0:
                print(f"     - {status_display}: {count} submissions")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Status Dropdown Test Complete!")
    return True

if __name__ == "__main__":
    try:
        test_status_dropdown()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)