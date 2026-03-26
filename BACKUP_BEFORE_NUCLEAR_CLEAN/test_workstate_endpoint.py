#!/usr/bin/env python3
"""
Test script to check workstate assets endpoint directly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import WorkItemAttachment

def test_workstate_endpoint():
    print("=== TESTING WORKSTATE ASSETS ENDPOINT ===\n")
    
    # Create test client
    client = Client()
    
    # Get or create admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    
    if not admin_user:
        print("No admin user found. Creating one...")
        admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
    
    print(f"Using admin user: {admin_user.username}")
    
    # Login
    client.force_login(admin_user)
    
    # Test the endpoint
    print("\n1. Testing workstate assets endpoint...")
    response = client.get('/admin/documents/workstate-assets/')
    
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.get('Content-Type', 'N/A')}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        print(f"Content Length: {len(content)} characters")
        
        # Check if files are in the response
        if 'workstate_files' in content:
            print("✓ Template contains 'workstate_files' variable")
        else:
            print("✗ Template does NOT contain 'workstate_files' variable")
            
        if 'No workstate assets found' in content:
            print("✗ Shows 'No workstate assets found' message")
        else:
            print("✓ Does NOT show 'No workstate assets found' message")
            
        # Check for file items
        if 'fm-item file' in content:
            print("✓ Contains file items")
        else:
            print("✗ Does NOT contain file items")
            
        # Check for specific file names from our debug
        if 'BLACK_BOARD_POW.xls' in content:
            print("✓ Contains expected file: BLACK_BOARD_POW.xls")
        else:
            print("✗ Does NOT contain expected file: BLACK_BOARD_POW.xls")
            
        if 'FINAL-CAPSTONE-PPT.pptx' in content:
            print("✓ Contains expected file: FINAL-CAPSTONE-PPT.pptx")
        else:
            print("✗ Does NOT contain expected file: FINAL-CAPSTONE-PPT.pptx")
    else:
        print(f"ERROR: Response status {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')[:500]}...")
    
    # Test AJAX request
    print("\n2. Testing AJAX request...")
    ajax_response = client.get('/admin/documents/workstate-assets/', 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    print(f"AJAX Status Code: {ajax_response.status_code}")
    
    if ajax_response.status_code == 200:
        try:
            import json
            data = json.loads(ajax_response.content.decode('utf-8'))
            print(f"AJAX Response Status: {data.get('status', 'N/A')}")
            print(f"AJAX Total Files: {data.get('total_files', 'N/A')}")
            
            if 'html' in data:
                html_content = data['html']
                print(f"AJAX HTML Length: {len(html_content)} characters")
                
                if 'BLACK_BOARD_POW.xls' in html_content:
                    print("✓ AJAX HTML contains expected file: BLACK_BOARD_POW.xls")
                else:
                    print("✗ AJAX HTML does NOT contain expected file: BLACK_BOARD_POW.xls")
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse AJAX JSON response: {e}")
            print(f"Raw response: {ajax_response.content.decode('utf-8')[:200]}...")
    
    # Check database directly
    print("\n3. Database check...")
    total_attachments = WorkItemAttachment.objects.count()
    accepted_attachments = WorkItemAttachment.objects.filter(acceptance_status="accepted").count()
    print(f"Total attachments: {total_attachments}")
    print(f"Accepted attachments: {accepted_attachments}")

if __name__ == "__main__":
    test_workstate_endpoint()