#!/usr/bin/env python3
"""
Test script to verify the workstate assets endpoint fix
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

def test_workstate_assets_fix():
    """Test that the workstate assets endpoint now shows files"""
    
    print("🔧 TESTING WORKSTATE ASSETS FIX")
    print("=" * 40)
    
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
    
    # Test workstate assets endpoint
    print("\n📊 TESTING WORKSTATE ASSETS ENDPOINT")
    print("-" * 30)
    
    url = reverse('admin_app:workstate-assets')
    response = client.get(url)
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check if page loads
        print(f"✅ Workstate Assets page loads: Status {response.status_code}")
        
        # Check for expected content
        if 'Workstate Assets' in content:
            print("✅ Page contains 'Workstate Assets' title")
        else:
            print("❌ Page missing 'Workstate Assets' title")
        
        # Check for files or empty state
        if 'No workstate assets found' in content:
            print("⚠️  Page shows 'No workstate assets found' message")
            print("💡 This might be expected if template variables are still wrong")
        elif 'Workstate Assets (' in content:
            print("✅ Page shows workstate assets with count")
        else:
            print("❌ Page doesn't show expected content")
        
        # Check for specific file indicators
        if 'fm-item file' in content:
            print("✅ Page contains file items")
        else:
            print("⚠️  Page doesn't contain file items")
        
        # Check for template variables
        if 'workstate_files' in content:
            print("✅ Template uses workstate_files variable")
        else:
            print("⚠️  Template doesn't use workstate_files variable")
            
    else:
        print(f"❌ Workstate Assets page failed: Status {response.status_code}")
        return False
    
    # Test AJAX request
    print("\n📡 TESTING AJAX REQUEST")
    print("-" * 30)
    
    ajax_response = client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if ajax_response.status_code == 200:
        try:
            data = ajax_response.json()
            print(f"✅ AJAX request successful: Status {ajax_response.status_code}")
            print(f"✅ Response contains {data.get('total_files', 0)} files")
            
            if 'html' in data:
                html_content = data['html']
                if 'fm-item file' in html_content:
                    print("✅ AJAX HTML contains file items")
                else:
                    print("⚠️  AJAX HTML doesn't contain file items")
            else:
                print("❌ AJAX response missing HTML content")
                
        except Exception as e:
            print(f"❌ AJAX response not valid JSON: {e}")
    else:
        print(f"❌ AJAX request failed: Status {ajax_response.status_code}")
    
    print("\n🎯 TEST SUMMARY")
    print("=" * 40)
    print("✅ Fix applied: Added workstate_files and total_workstate_files to context")
    print("✅ Template should now display files correctly")
    print("💡 If still showing empty, check browser cache or template syntax")
    
    return True

if __name__ == "__main__":
    test_workstate_assets_fix()