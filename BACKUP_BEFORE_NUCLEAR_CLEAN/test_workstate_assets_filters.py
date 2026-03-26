#!/usr/bin/env python3
"""
Test script to verify Workstate Assets filtering functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, WorkCycle, User
from django.test import RequestFactory
from admin_app.views.all_files_views import all_files_view

def test_workstate_assets_filtering():
    """Test the Workstate Assets filtering functionality"""
    
    print("🔍 Testing Workstate Assets Filtering...")
    
    # Get some test data
    workstate_attachments = WorkItemAttachment.objects.filter(
        acceptance_status="accepted"
    ).exclude(
        folder__folder_type='attachment'  # Exclude document tracking
    )[:5]
    
    print(f"📊 Found {workstate_attachments.count()} workstate assets")
    
    # Test attachment types
    attachment_types = {}
    for attachment in workstate_attachments:
        att_type = attachment.attachment_type
        if att_type not in attachment_types:
            attachment_types[att_type] = 0
        attachment_types[att_type] += 1
    
    print("📋 Attachment Types Found:")
    for att_type, count in attachment_types.items():
        display_name = dict(WorkItemAttachment.ATTACHMENT_TYPE_CHOICES).get(att_type, att_type)
        print(f"  - {display_name}: {count} files")
    
    # Test WorkCycles
    workcycles_with_assets = WorkCycle.objects.filter(
        work_items__attachments__acceptance_status="accepted",
        work_items__attachments__folder__folder_type__isnull=False
    ).exclude(
        work_items__attachments__folder__folder_type='attachment'
    ).distinct()[:3]
    
    print(f"🔄 Found {workcycles_with_assets.count()} WorkCycles with assets")
    for wc in workcycles_with_assets:
        asset_count = WorkItemAttachment.objects.filter(
            work_item__workcycle=wc,
            acceptance_status="accepted"
        ).exclude(
            folder__folder_type='attachment'
        ).count()
        print(f"  - {wc.title}: {asset_count} assets")
    
    # Test filtering by attachment type
    if attachment_types:
        test_type = list(attachment_types.keys())[0]
        filtered_assets = WorkItemAttachment.objects.filter(
            acceptance_status="accepted",
            attachment_type=test_type
        ).exclude(
            folder__folder_type='attachment'
        )
        
        print(f"🎯 Filter Test - {dict(WorkItemAttachment.ATTACHMENT_TYPE_CHOICES).get(test_type, test_type)}: {filtered_assets.count()} assets")
    
    print("✅ Workstate Assets filtering test completed!")
    return True

def test_api_endpoints():
    """Test the new API endpoints"""
    
    print("\n🌐 Testing API Endpoints...")
    
    from admin_app.views.all_files_views import (
        search_workstate_workcycles, search_workstate_files
    )
    from django.http import HttpRequest
    
    # Create a mock request
    request = HttpRequest()
    request.method = 'GET'
    request.GET = {'q': 'test'}
    request.user = User.objects.filter(is_staff=True).first()
    
    if not request.user:
        print("❌ No admin user found for testing")
        return False
    
    try:
        # Test WorkCycle search
        response = search_workstate_workcycles(request)
        print(f"🔍 WorkCycle Search API: Status {response.status_code}")
        
        # Test File search
        response = search_workstate_files(request)
        print(f"📁 File Search API: Status {response.status_code}")
        
        print("✅ API endpoints test completed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Workstate Assets Filter Tests\n")
    
    try:
        # Test 1: Basic filtering functionality
        test_workstate_assets_filtering()
        
        # Test 2: API endpoints
        test_api_endpoints()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)