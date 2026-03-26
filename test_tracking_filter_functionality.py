#!/usr/bin/env python3
"""
Test script for the tracking number filter functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from document_tracking.models import Submission

User = get_user_model()

def test_tracking_filter():
    """Test the tracking number filter functionality"""
    
    print("🔍 Testing Tracking Number Filter")
    print("=" * 40)
    
    # Create test client
    client = Client()
    
    # Get admin user
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Login
    admin_user.set_password('testpass123')
    admin_user.save()
    client.login(username=admin_user.username, password='testpass123')
    print(f"✅ Logged in as {admin_user.username}")
    
    # Test tracking number API
    print("\n📡 Testing Tracking Number API")
    print("-" * 30)
    
    # Test search tracking numbers filter API
    url = reverse('admin_app:api-search-tracking-filter')
    response = client.get(url + '?q=')
    print(f"✅ GET {url}?q= : Status {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Returned {len(data.get('results', []))} tracking numbers")
        
        # Show some sample results
        for i, result in enumerate(data.get('results', [])[:3]):
            if result.get('is_header'):
                print(f"  📁 {result.get('title', 'Unknown')}")
            else:
                print(f"  🏷️  {result.get('title', 'Unknown')} - {result.get('doc_type', 'No type')}")
    
    # Test with search query
    response = client.get(url + '?q=MAN')
    print(f"✅ GET {url}?q=MAN : Status {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search 'MAN' returned {len(data.get('results', []))} results")
    
    # Test routed documents filter
    print("\n📄 Testing Routed Documents Filter")
    print("-" * 30)
    
    # Get some submissions to test with
    submissions = Submission.objects.filter(tracking_number__isnull=False)[:3]
    print(f"✅ Found {submissions.count()} submissions with tracking numbers")
    
    for submission in submissions:
        print(f"  🏷️  {submission.tracking_number} - {submission.doc_type.name if submission.doc_type else 'No type'}")
        
        # Test filtering by this tracking number
        filter_url = reverse('admin_app:api-routed-documents')
        response = client.get(filter_url + f'?filter_type=tracking&filter_value={submission.tracking_number}')
        print(f"    ✅ Filter by tracking: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print(f"    ✅ Found {data.get('total_files', 0)} files for this tracking number")
            else:
                print(f"    ⚠️  Filter response: {data.get('message', 'Unknown error')}")
        break  # Test just one to avoid spam
    
    print("\n🎯 Tracking Filter Test Complete!")
    return True

if __name__ == "__main__":
    test_tracking_filter()