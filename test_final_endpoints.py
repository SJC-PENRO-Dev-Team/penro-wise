#!/usr/bin/env python3
"""
Test script to verify the final state of endpoints after cleanup
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

def test_endpoints():
    print("=== TESTING FINAL ENDPOINT STATE ===\n")
    
    # Create test client
    client = Client()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    client.force_login(admin_user)
    
    # Test 1: Verify accepted-files endpoint is removed
    print("1. Testing accepted-files endpoint removal...")
    try:
        url = reverse('admin_app:accepted-files')
        print(f"✗ ERROR: accepted-files URL still exists: {url}")
    except NoReverseMatch:
        print("✓ accepted-files endpoint successfully removed")
    
    # Test 2: Test routed documents endpoint
    print("\n2. Testing routed documents endpoint...")
    try:
        url = reverse('admin_app:routed-documents')
        response = client.get(url)
        print(f"✓ Routed documents endpoint working: {url} (Status: {response.status_code})")
    except NoReverseMatch:
        print("✗ ERROR: routed-documents endpoint not found")
    
    # Test 3: Test workstate assets endpoint
    print("\n3. Testing workstate assets endpoint...")
    try:
        url = reverse('admin_app:workstate-assets')
        response = client.get(url)
        print(f"✓ Workstate assets endpoint working: {url} (Status: {response.status_code})")
        
        # Test AJAX request
        ajax_response = client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        if ajax_response.status_code == 200:
            import json
            data = json.loads(ajax_response.content.decode('utf-8'))
            print(f"✓ AJAX request working - Total files: {data.get('total_files', 'N/A')}")
        else:
            print(f"✗ AJAX request failed: {ajax_response.status_code}")
            
    except NoReverseMatch:
        print("✗ ERROR: workstate-assets endpoint not found")
    
    # Test 4: Check if all-files endpoint exists (should not)
    print("\n4. Testing all-files endpoint removal...")
    try:
        # Try different possible names
        possible_names = ['all-files', 'all-files-uploaded', 'accepted-files']
        for name in possible_names:
            try:
                url = reverse(f'admin_app:{name}')
                print(f"✗ ERROR: {name} URL still exists: {url}")
            except NoReverseMatch:
                print(f"✓ {name} endpoint successfully removed")
    except Exception as e:
        print(f"Error testing all-files: {e}")
    
    print("\n=== ENDPOINT CLEANUP COMPLETE ===")

if __name__ == "__main__":
    test_endpoints()