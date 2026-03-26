#!/usr/bin/env python3
"""
Test script to verify workstate assets are displaying correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_workstate_display():
    print("=== TESTING WORKSTATE ASSETS DISPLAY ===\n")
    
    # Create test client
    client = Client()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    # Test the workstate assets page
    print("1. Testing workstate assets page...")
    response = client.get('/admin/documents/workstate-assets/')
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Check for expected files
        expected_files = ['BLACK_BOARD_POW.xls', 'FINAL-CAPSTONE-PPT.pptx']
        files_found = []
        
        for filename in expected_files:
            if filename in content:
                files_found.append(filename)
                print(f"✓ Found file: {filename}")
            else:
                print(f"✗ Missing file: {filename}")
        
        # Check for empty state message
        if 'No workstate assets found' in content:
            print("✗ Shows 'No workstate assets found' message (should not)")
        else:
            print("✓ Does not show 'No workstate assets found' message")
        
        # Check for file grid
        if 'fm-grid' in content and 'workstateGrid' in content:
            print("✓ Contains file grid structure")
        else:
            print("✗ Missing file grid structure")
        
        # Check for file count
        if 'Workstate Assets (2)' in content:
            print("✓ Shows correct file count: 2")
        elif 'Workstate Assets (' in content:
            import re
            match = re.search(r'Workstate Assets \((\d+)\)', content)
            if match:
                count = match.group(1)
                print(f"? Shows file count: {count} (expected 2)")
            else:
                print("✗ File count not found")
        else:
            print("✗ File count section not found")
        
        print(f"\nSummary: Found {len(files_found)}/{len(expected_files)} expected files")
        
    else:
        print(f"✗ Page failed to load: Status {response.status_code}")
    
    # Test AJAX request
    print("\n2. Testing AJAX request...")
    ajax_response = client.get('/admin/documents/workstate-assets/', 
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if ajax_response.status_code == 200:
        import json
        try:
            data = json.loads(ajax_response.content.decode('utf-8'))
            print(f"✓ AJAX Status: {data.get('status')}")
            print(f"✓ AJAX Total Files: {data.get('total_files')}")
            
            html_content = data.get('html', '')
            ajax_files_found = []
            
            for filename in expected_files:
                if filename in html_content:
                    ajax_files_found.append(filename)
            
            print(f"✓ AJAX HTML contains {len(ajax_files_found)}/{len(expected_files)} expected files")
            
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse AJAX response: {e}")
    else:
        print(f"✗ AJAX request failed: Status {ajax_response.status_code}")

if __name__ == "__main__":
    test_workstate_display()