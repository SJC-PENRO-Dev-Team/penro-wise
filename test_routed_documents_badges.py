#!/usr/bin/env python3
"""
Test script to verify routed documents badges are displayed in unfiltered view.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_routed_documents_badges():
    """Test that unfiltered routed documents show badges"""
    
    print("🧪 Testing Routed Documents Badges in Unfiltered View")
    print("=" * 60)
    
    # Create test client
    client = Client()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Test AJAX request for routed documents (unfiltered)
    print("📋 Testing AJAX Routed Documents Request")
    response = client.get('/admin/documents/all-files/?view=routed', 
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        print(f"✅ AJAX request successful (Status: {response.status_code})")
        
        try:
            data = response.json()
            if data.get('status') == 'success':
                html = data.get('html', '')
                
                # Check for badge elements in HTML
                badge_indicators = [
                    'badge',  # General badge class
                    'doc_type',  # Document type attribute
                    'status',  # Status attribute
                    'Document',  # Document badge text
                    'MANUAL INPUT',  # Document type text
                    'Approved',  # Status text
                ]
                
                found_badges = []
                for indicator in badge_indicators:
                    if indicator in html:
                        found_badges.append(indicator)
                
                print(f"📊 Total files returned: {data.get('total_files', 0)}")
                print(f"📊 Badge indicators found: {len(found_badges)}/{len(badge_indicators)}")
                print(f"✅ Found badges: {', '.join(found_badges)}")
                
                if len(found_badges) >= 3:  # At least some badge indicators
                    print("✅ Badges are present in unfiltered routed documents")
                    return True
                else:
                    print("⚠️  Limited badge indicators found")
                    print("📄 HTML preview:")
                    print(html[:500] + "..." if len(html) > 500 else html)
                    return False
            else:
                print(f"⚠️  AJAX response status: {data.get('status', 'unknown')}")
                return False
        except Exception as e:
            print(f"❌ Failed to parse response: {e}")
            return False
    else:
        print(f"❌ AJAX request failed (Status: {response.status_code})")
        return False

if __name__ == '__main__':
    try:
        success = test_routed_documents_badges()
        if success:
            print("\n🎯 ROUTED DOCUMENTS BADGES: WORKING")
        else:
            print("\n❌ ROUTED DOCUMENTS BADGES: NEED FIXING")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()