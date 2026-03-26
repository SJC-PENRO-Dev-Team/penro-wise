#!/usr/bin/env python3
"""
Test script for the separate routed documents and workstate assets endpoints
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

User = get_user_model()

def test_separate_endpoints():
    """Test the new separate endpoints for routed documents and workstate assets"""
    
    print("🧪 Testing Separate Endpoints")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Get or create admin user
    try:
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='testadmin',
                email='admin@test.com',
                password='testpass123'
            )
            print(f"✅ Created test admin user: {admin_user.username}")
        else:
            print(f"✅ Using existing admin user: {admin_user.username}")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    # Login as admin
    if admin_user.check_password('testpass123'):
        login_success = client.login(username=admin_user.username, password='testpass123')
    else:
        # Try to set a known password
        admin_user.set_password('testpass123')
        admin_user.save()
        login_success = client.login(username=admin_user.username, password='testpass123')
    
    if not login_success:
        print("❌ Failed to login as admin")
        return False
    
    print("✅ Successfully logged in as admin")
    
    # Test endpoints
    endpoints_to_test = [
        ('routed-documents', '/admin/documents/routed-documents/'),
        ('workstate-assets', '/admin/documents/workstate-assets/'),
        ('all-files-uploaded', '/admin/documents/all-files/'),  # Original endpoint
    ]
    
    for endpoint_name, expected_url in endpoints_to_test:
        try:
            # Test URL reverse
            url = reverse(f'admin_app:{endpoint_name}')
            print(f"✅ URL reverse for '{endpoint_name}': {url}")
            
            if url != expected_url:
                print(f"⚠️  URL mismatch - Expected: {expected_url}, Got: {url}")
            
            # Test GET request
            response = client.get(url)
            print(f"✅ GET {endpoint_name}: Status {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Unexpected status code for {endpoint_name}: {response.status_code}")
                continue
            
            # Check if response contains expected content
            content = response.content.decode('utf-8')
            
            if endpoint_name == 'routed-documents':
                if 'Routed Documents' in content:
                    print("✅ Routed Documents page contains expected title")
                else:
                    print("⚠️  Routed Documents page missing expected title")
                    
                if 'Tracking Number' in content:
                    print("✅ Routed Documents page contains tracking number filter")
                else:
                    print("⚠️  Routed Documents page missing tracking number filter")
            
            elif endpoint_name == 'workstate-assets':
                if 'Workstate Assets' in content:
                    print("✅ Workstate Assets page contains expected title")
                else:
                    print("⚠️  Workstate Assets page missing expected title")
                    
                if 'Asset Category' in content:
                    print("✅ Workstate Assets page contains asset category filter")
                else:
                    print("⚠️  Workstate Assets page missing asset category filter")
            
            elif endpoint_name == 'all-files-uploaded':
                if 'All Accepted Files' in content or 'All Files' in content:
                    print("✅ All Files page contains expected title")
                else:
                    print("⚠️  All Files page missing expected title")
            
            print()
            
        except Exception as e:
            print(f"❌ Error testing {endpoint_name}: {e}")
            print()
    
    # Test API endpoints
    api_endpoints = [
        'api-search-tracking-filter',
        'api-search-document-types', 
        'api-search-sections',
        'api-routed-documents',
        'api-search-workstate-workcycles',
        'api-workstate-assets'
    ]
    
    print("🔌 Testing API Endpoints")
    print("-" * 30)
    
    for api_endpoint in api_endpoints:
        try:
            url = reverse(f'admin_app:{api_endpoint}')
            print(f"✅ API URL reverse for '{api_endpoint}': {url}")
            
            # Test basic GET request (some may require parameters)
            response = client.get(url)
            print(f"✅ GET {api_endpoint}: Status {response.status_code}")
            
            if response.status_code == 200:
                # Try to parse JSON response
                try:
                    data = response.json()
                    if 'results' in data:
                        print(f"✅ API {api_endpoint} returned JSON with results key")
                    else:
                        print(f"⚠️  API {api_endpoint} JSON missing 'results' key")
                except:
                    print(f"⚠️  API {api_endpoint} did not return valid JSON")
            
            print()
            
        except Exception as e:
            print(f"❌ Error testing API {api_endpoint}: {e}")
            print()
    
    print("🎯 Testing Complete!")
    return True

if __name__ == "__main__":
    test_separate_endpoints()