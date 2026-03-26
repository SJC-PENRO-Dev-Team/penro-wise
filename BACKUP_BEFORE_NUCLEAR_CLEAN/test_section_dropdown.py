#!/usr/bin/env python3
"""
Test script for Section Dropdown Functionality
Tests the new dropdown select with submission counts and "Folder Section" naming
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from admin_app.views.routed_documents_api import search_sections
from document_tracking.models import Section, Submission

User = get_user_model()

def test_section_dropdown():
    """Test the section dropdown functionality"""
    print("🔍 Testing Section (Folder Section) Dropdown")
    print("=" * 50)
    
    # Get test user
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ No admin user found")
        return False
    
    factory = RequestFactory()
    
    # Test 1: Load all sections (no query)
    print("\n1. Loading All Sections (Dropdown)")
    try:
        request = factory.get('/api/search-sections/', {'q': ''})
        request.user = user
        response = search_sections(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Total sections: {len(data.get('results', []))}")
            
            if data.get('results'):
                print("   📊 Section breakdown:")
                for section in data['results']:
                    print(f"     - {section['title']}: {section['submission_count']} submissions")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Search specific section
    print("\n2. Search Specific Section")
    try:
        request = factory.get('/api/search-sections/', {'q': 'license'})
        request.user = user
        response = search_sections(request)
        
        if response.status_code == 200:
            data = json.loads(response.content.decode('utf-8'))
            print(f"   ✓ Status: {response.status_code}")
            print(f"   ✓ Filtered results: {len(data.get('results', []))}")
            
            if data.get('results'):
                for section in data['results']:
                    print(f"     - {section['title']}: {section['submission_count']} submissions")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check section data
    print("\n3. Database Section Distribution")
    try:
        total_sections = Section.objects.filter(is_active=True).count()
        print(f"   📈 Total active sections: {total_sections}")
        
        sections_with_submissions = Section.objects.filter(is_active=True)
        for section in sections_with_submissions:
            count = Submission.objects.filter(assigned_section=section).count()
            print(f"     - {section.display_name or section.name}: {count} submissions")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Section (Folder Section) Dropdown Test Complete!")
    return True

if __name__ == "__main__":
    try:
        test_section_dropdown()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)