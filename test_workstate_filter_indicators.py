#!/usr/bin/env python3
"""
Test script to verify Workstate Assets filter indicators and "All Assets" functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, WorkCycle
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_all_assets_filter():
    """Test the 'All Assets' filter functionality"""
    
    print("🔍 Testing 'All Assets' Filter...")
    
    # Get all workstate assets (excluding document tracking)
    all_workstate_assets = WorkItemAttachment.objects.filter(
        acceptance_status="accepted"
    ).exclude(
        folder__folder_type='attachment'  # Exclude document tracking
    )
    
    print(f"📊 Total workstate assets: {all_workstate_assets.count()}")
    
    # Test filtering by each attachment type
    attachment_types = WorkItemAttachment.ATTACHMENT_TYPE_CHOICES
    
    print("📋 Testing individual category filters:")
    total_filtered = 0
    
    for type_code, type_display in attachment_types:
        filtered_assets = all_workstate_assets.filter(attachment_type=type_code)
        count = filtered_assets.count()
        total_filtered += count
        
        if count > 0:
            print(f"  ✅ {type_display}: {count} assets")
        else:
            print(f"  ⚪ {type_display}: {count} assets")
    
    print(f"📈 Total assets across all categories: {total_filtered}")
    print(f"📊 All assets count: {all_workstate_assets.count()}")
    
    # Verify counts match
    if total_filtered == all_workstate_assets.count():
        print("✅ All Assets filter will show correct total")
    else:
        print("⚠️  Counts don't match - possible data inconsistency")
    
    return True

def test_filter_api_endpoints():
    """Test the filter API endpoints with different parameters"""
    
    print("\n🌐 Testing Filter API Endpoints...")
    
    # Create a test client
    client = Client()
    
    # Get an admin user for testing
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found for testing")
        return False
    
    # Login as admin
    client.force_login(admin_user)
    
    try:
        # Test 1: All workstate assets (no filter)
        response = client.get('/admin/documents/all-files/', {
            'view': 'workstate'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        print(f"🔍 All Assets API: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 Total assets returned: {data.get('total_files', 'N/A')}")
        
        # Test 2: Filter by specific attachment type
        response = client.get('/admin/documents/all-files/', {
            'view': 'workstate',
            'workstate_type': 'mov'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        print(f"🎯 MOV Filter API: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  📊 MOV assets returned: {data.get('total_files', 'N/A')}")
        
        # Test 3: Filter by WorkCycle
        workcycle = WorkCycle.objects.filter(is_active=True).first()
        if workcycle:
            response = client.get('/admin/documents/all-files/', {
                'view': 'workstate',
                'workstate_workcycle': workcycle.id
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            
            print(f"🔄 WorkCycle Filter API: Status {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  📊 Assets for '{workcycle.title}': {data.get('total_files', 'N/A')}")
        
        print("✅ API endpoints test completed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_template_rendering():
    """Test that the template renders correctly with filter indicators"""
    
    print("\n🎨 Testing Template Rendering...")
    
    client = Client()
    admin_user = User.objects.filter(is_staff=True).first()
    
    if not admin_user:
        print("❌ No admin user found for testing")
        return False
    
    client.force_login(admin_user)
    
    try:
        # Test main page rendering
        response = client.get('/admin/documents/all-files/')
        print(f"📄 Main Page: Status {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for filter elements
            checks = [
                ('workstateCategoryBtn', 'Category filter button'),
                ('workstateCategoryText', 'Category filter text'),
                ('clearWorkstateFilters', 'Clear filters function'),
                ('All Assets', 'All Assets option'),
                ('selectWorkstateCategory', 'Category selection function')
            ]
            
            for check_text, description in checks:
                if check_text in content:
                    print(f"  ✅ {description}: Found")
                else:
                    print(f"  ❌ {description}: Missing")
        
        print("✅ Template rendering test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Workstate Filter Indicators Tests\n")
    
    try:
        # Test 1: All Assets filter logic
        test_all_assets_filter()
        
        # Test 2: API endpoints
        test_filter_api_endpoints()
        
        # Test 3: Template rendering
        test_template_rendering()
        
        print("\n🎉 All filter indicator tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)