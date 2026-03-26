#!/usr/bin/env python3
"""
Debug script to check template context for workstate assets
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from admin_app.views.all_files_views import workstate_assets_view

def debug_template_context():
    print("=== DEBUGGING TEMPLATE CONTEXT ===\n")
    
    # Create request factory
    factory = RequestFactory()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    
    # Create request
    request = factory.get('/admin/documents/workstate-assets/')
    request.user = admin_user
    
    # Call the view directly
    response = workstate_assets_view(request)
    
    print(f"Response status: {response.status_code}")
    
    # Check if it's a template response
    if hasattr(response, 'context_data'):
        context = response.context_data
        print(f"Context keys: {list(context.keys())}")
        
        if 'workstate_files' in context:
            workstate_files = context['workstate_files']
            print(f"workstate_files type: {type(workstate_files)}")
            print(f"workstate_files length: {len(workstate_files)}")
            print(f"workstate_files content: {workstate_files[:2] if workstate_files else 'Empty'}")
        else:
            print("workstate_files NOT in context")
            
        if 'total_workstate_files' in context:
            print(f"total_workstate_files: {context['total_workstate_files']}")
        else:
            print("total_workstate_files NOT in context")
    else:
        print("No context_data available")
        
    # Test AJAX request
    print("\n=== TESTING AJAX REQUEST ===")
    ajax_request = factory.get('/admin/documents/workstate-assets/')
    ajax_request.user = admin_user
    ajax_request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
    
    ajax_response = workstate_assets_view(ajax_request)
    print(f"AJAX Response status: {ajax_response.status_code}")
    
    if hasattr(ajax_response, 'content'):
        import json
        try:
            data = json.loads(ajax_response.content.decode('utf-8'))
            print(f"AJAX Response keys: {list(data.keys())}")
            print(f"AJAX Status: {data.get('status')}")
            print(f"AJAX Total files: {data.get('total_files')}")
            
            if 'html' in data:
                html = data['html']
                print(f"HTML length: {len(html)}")
                
                # Check for key elements
                if 'workstate_files' in html:
                    print("✓ HTML contains 'workstate_files'")
                else:
                    print("✗ HTML does NOT contain 'workstate_files'")
                    
                if 'No workstate assets found' in html:
                    print("✗ HTML shows 'No workstate assets found'")
                else:
                    print("✓ HTML does NOT show 'No workstate assets found'")
                    
                # Show first 500 chars of HTML
                print(f"\nFirst 500 chars of HTML:\n{html[:500]}...")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")

if __name__ == "__main__":
    debug_template_context()