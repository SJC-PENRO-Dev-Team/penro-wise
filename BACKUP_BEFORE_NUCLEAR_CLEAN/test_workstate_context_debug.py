#!/usr/bin/env python3
"""
Debug script to check the exact context being passed to workstate assets template
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
from django.template.loader import render_to_string

User = get_user_model()

def test_workstate_context():
    """Test the exact context being passed to workstate assets"""
    
    print("🔍 DEBUGGING WORKSTATE ASSETS CONTEXT")
    print("=" * 50)
    
    # Setup
    client = Client()
    admin_user = User.objects.filter(is_staff=True).first()
    admin_user.set_password('testpass123')
    admin_user.save()
    client.login(username=admin_user.username, password='testpass123')
    
    # Manually call the view to see the context
    from admin_app.views.all_files_views import workstate_assets_view
    from django.test import RequestFactory
    
    factory = RequestFactory()
    request = factory.get('/admin/documents/workstate-assets/')
    request.user = admin_user
    
    # Call the view directly
    response = workstate_assets_view(request)
    
    print(f"✅ View response status: {response.status_code}")
    
    # Check the response content
    content = response.content.decode('utf-8')
    
    # Look for specific indicators
    print(f"\n📊 CONTENT ANALYSIS")
    print("-" * 30)
    
    if 'workstate_files' in content:
        print("✅ Content contains 'workstate_files'")
    else:
        print("❌ Content missing 'workstate_files'")
    
    if 'total_workstate_files' in content:
        print("✅ Content contains 'total_workstate_files'")
    else:
        print("❌ Content missing 'total_workstate_files'")
    
    if 'No workstate assets found' in content:
        print("⚠️  Content shows 'No workstate assets found'")
    else:
        print("✅ Content doesn't show empty message")
    
    if 'Workstate Assets (' in content:
        print("✅ Content shows workstate assets with count")
    else:
        print("❌ Content doesn't show count")
    
    # Test the partial template directly
    print(f"\n🧪 TESTING PARTIAL TEMPLATE DIRECTLY")
    print("-" * 30)
    
    # Create test context
    test_context = {
        'workstate_files': [
            {
                'id': 1,
                'name': 'test-file.pdf',
                'is_link': False,
                'is_link_group': False,
                'uploaded_at': '2026-03-17',
                'attachment_type': 'document',
                'attachment_type_display': 'Document',
                'workcycle': {'title': 'Test WorkCycle'}
            }
        ],
        'total_workstate_files': 1
    }
    
    try:
        partial_html = render_to_string(
            'admin/page/partials/_workstate_assets_content.html',
            test_context
        )
        
        if 'test-file.pdf' in partial_html:
            print("✅ Partial template renders test file correctly")
        else:
            print("❌ Partial template doesn't render test file")
            
        if 'No workstate assets found' in partial_html:
            print("❌ Partial template shows empty message with test data")
        else:
            print("✅ Partial template doesn't show empty message with test data")
            
    except Exception as e:
        print(f"❌ Error rendering partial template: {e}")
    
    # Test with empty context
    print(f"\n🔄 TESTING WITH EMPTY CONTEXT")
    print("-" * 30)
    
    empty_context = {
        'workstate_files': [],
        'total_workstate_files': 0
    }
    
    try:
        empty_html = render_to_string(
            'admin/page/partials/_workstate_assets_content.html',
            empty_context
        )
        
        if 'No workstate assets found' in empty_html:
            print("✅ Partial template shows empty message with empty data")
        else:
            print("❌ Partial template doesn't show empty message with empty data")
            
    except Exception as e:
        print(f"❌ Error rendering empty partial template: {e}")
    
    print(f"\n🎯 DIAGNOSIS")
    print("=" * 50)
    print("The issue is likely that the main template loads before")
    print("the context is properly set, but AJAX requests work correctly.")
    print("This suggests the initial page load has incorrect context.")

if __name__ == "__main__":
    test_workstate_context()