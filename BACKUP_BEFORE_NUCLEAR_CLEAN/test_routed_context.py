#!/usr/bin/env python3
"""
Test script to verify routed documents context has badge attributes.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from admin_app.views.all_files_views import all_files_view

def test_routed_documents_context():
    """Test that routed documents context includes badge attributes"""
    
    print("🧪 Testing Routed Documents Context for Badges")
    print("=" * 60)
    
    # Create request factory
    factory = RequestFactory()
    
    # Get admin user
    User = get_user_model()
    admin_user = User.objects.filter(is_staff=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Test AJAX request for routed documents
    print("📋 Testing AJAX Routed Documents Context")
    request = factory.get('/admin/documents/all-files/?view=routed')
    request.user = admin_user
    request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
    
    try:
        response = all_files_view(request)
        print(f"✅ View executed successfully (Status: {response.status_code})")
        
        if hasattr(response, 'content'):
            import json
            data = json.loads(response.content.decode('utf-8'))
            
            if data.get('status') == 'success':
                html = data.get('html', '')
                total_files = data.get('total_files', 0)
                
                print(f"📊 Total routed files: {total_files}")
                
                # Check for badge-related content in HTML
                badge_checks = {
                    'Document Type Badge': 'MANUAL INPUT' in html,
                    'Status Badge': 'Approved' in html,
                    'Document Badge': 'Document' in html,
                    'Badge CSS Class': 'badge' in html,
                    'Color Styling': 'background:' in html or 'color:' in html,
                }
                
                print("\n📋 Badge Content Analysis:")
                for check_name, found in badge_checks.items():
                    status = "✅" if found else "❌"
                    print(f"   {status} {check_name}: {found}")
                
                # Count successful checks
                successful_checks = sum(badge_checks.values())
                total_checks = len(badge_checks)
                
                print(f"\n📊 Badge checks passed: {successful_checks}/{total_checks}")
                
                if successful_checks >= 3:
                    print("✅ Routed documents have badge attributes")
                    return True
                else:
                    print("⚠️  Limited badge content found")
                    print("\n📄 HTML Sample (first 300 chars):")
                    print(html[:300] + "..." if len(html) > 300 else html)
                    return False
            else:
                print(f"⚠️  Response status: {data.get('status', 'unknown')}")
                return False
        else:
            print("❌ No content in response")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = test_routed_documents_context()
        if success:
            print("\n🎯 ROUTED DOCUMENTS BADGES CONTEXT: WORKING")
        else:
            print("\n❌ ROUTED DOCUMENTS BADGES CONTEXT: NEEDS FIXING")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()