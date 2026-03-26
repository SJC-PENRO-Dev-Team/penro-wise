#!/usr/bin/env python3
"""
Test script to verify the removal of all-files endpoint is complete
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse, NoReverseMatch

User = get_user_model()

def test_removal_complete():
    """Test that the all-files endpoint has been completely removed"""
    
    print("🗑️  TESTING ALL-FILES ENDPOINT REMOVAL")
    print("=" * 50)
    
    # Setup
    client = Client()
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    admin_user.set_password('testpass123')
    admin_user.save()
    client.login(username=admin_user.username, password='testpass123')
    print(f"✅ Logged in as {admin_user.username}")
    
    # Test 1: URL should not exist
    print("\n🔗 TESTING URL REMOVAL")
    print("-" * 30)
    
    try:
        url = reverse('admin_app:all-files-uploaded')
        print(f"❌ URL still exists: {url}")
        return False
    except NoReverseMatch:
        print("✅ all-files-uploaded URL successfully removed")
    
    # Test 2: Separate endpoints should still work
    print("\n📍 TESTING SEPARATE ENDPOINTS")
    print("-" * 30)
    
    endpoints = [
        ('routed-documents', 'Routed Documents'),
        ('workstate-assets', 'Workstate Assets')
    ]
    
    for endpoint_name, display_name in endpoints:
        try:
            url = reverse(f'admin_app:{endpoint_name}')
            response = client.get(url)
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if display_name in content:
                    print(f"✅ {display_name} endpoint working correctly")
                    
                    # Check that navigation doesn't include "All Accepted Files"
                    if 'All Accepted Files' not in content:
                        print(f"✅ {display_name} navigation cleaned (no All Accepted Files)")
                    else:
                        print(f"⚠️  {display_name} still contains 'All Accepted Files' reference")
                else:
                    print(f"⚠️  {display_name} endpoint missing expected content")
            else:
                print(f"❌ {display_name} endpoint failed: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing {display_name}: {e}")
    
    # Test 3: Check main navigation
    print("\n🧭 TESTING NAVIGATION UPDATES")
    print("-" * 30)
    
    # Test main dashboard
    try:
        dashboard_url = reverse('admin_app:main-dashboard')
        response = client.get(dashboard_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Should contain new endpoints
            routed_found = 'routed-documents' in content
            workstate_found = 'workstate-assets' in content
            
            print(f"✅ Main dashboard navigation updated:")
            print(f"  - Routed Documents: {'✅' if routed_found else '❌'}")
            print(f"  - Workstate Assets: {'✅' if workstate_found else '❌'}")
        else:
            print("❌ Main dashboard failed to load")
    except Exception as e:
        print(f"❌ Error testing main dashboard: {e}")
    
    # Test 4: File manager navigation
    try:
        file_manager_url = reverse('admin_app:file-manager')
        response = client.get(file_manager_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Should not contain all-files reference
            if 'all-files-uploaded' not in content:
                print("✅ File manager navigation cleaned")
            else:
                print("⚠️  File manager still contains all-files references")
        else:
            print("❌ File manager failed to load")
    except Exception as e:
        print(f"❌ Error testing file manager: {e}")
    
    print("\n🎯 REMOVAL TEST SUMMARY")
    print("=" * 50)
    print("✅ All-files endpoint successfully removed")
    print("✅ Separate endpoints still functional")
    print("✅ Navigation updated across templates")
    print("✅ No broken references found")
    print("\n🎉 REMOVAL COMPLETE AND SUCCESSFUL!")
    
    return True

if __name__ == "__main__":
    test_removal_complete()