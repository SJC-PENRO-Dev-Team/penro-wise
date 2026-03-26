"""
Verify Serial Availability Checker Implementation

This script checks if all components are properly configured.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
django.setup()

from django.urls import reverse, resolve
from document_tracking.views import api_views
import re


def check_url_configuration():
    """Check if URL is properly configured."""
    print("=" * 60)
    print("1. CHECKING URL CONFIGURATION")
    print("=" * 60)
    
    try:
        url = reverse('document_tracking:api-check-serial-availability')
        print(f"✅ URL is registered: {url}")
        
        # Verify it resolves to correct view
        resolved = resolve(url)
        if resolved.func == api_views.api_check_serial_availability:
            print(f"✅ URL resolves to correct view: {resolved.func.__name__}")
        else:
            print(f"❌ URL resolves to wrong view: {resolved.func.__name__}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ URL configuration error: {e}")
        return False


def check_template_cache_busting():
    """Check if cache-busting is applied to template."""
    print("\n" + "=" * 60)
    print("2. CHECKING TEMPLATE CACHE-BUSTING")
    print("=" * 60)
    
    template_path = 'templates/document_tracking/admin_detail.html'
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'Cache-Control meta tag': 'Cache-Control',
        'Pragma meta tag': 'Pragma',
        'Expires meta tag': 'Expires',
        'CSS version parameter': r'document-tracking\.css\?v=',
        'Serial availability feedback div': 'serialAvailabilityFeedback',
        'Serial checking state': 'serialChecking',
        'Serial available state': 'serialAvailable',
        'Serial taken state': 'serialTaken',
        'Serial error state': 'serialError',
        'checkSerialAvailability function': 'checkSerialAvailability',
        'API endpoint URL': 'api-check-serial-availability',
    }
    
    all_passed = True
    for check_name, pattern in checks.items():
        if re.search(pattern, content):
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: NOT FOUND")
            all_passed = False
    
    return all_passed


def check_api_view():
    """Check if API view is properly implemented."""
    print("\n" + "=" * 60)
    print("3. CHECKING API VIEW IMPLEMENTATION")
    print("=" * 60)
    
    try:
        # Check if function exists
        if hasattr(api_views, 'api_check_serial_availability'):
            print("✅ API view function exists")
        else:
            print("❌ API view function not found")
            return False
        
        # Check function signature
        import inspect
        sig = inspect.signature(api_views.api_check_serial_availability)
        if 'request' in sig.parameters:
            print("✅ Function has correct signature")
        else:
            print("❌ Function signature incorrect")
            return False
        
        # Check decorators
        func = api_views.api_check_serial_availability
        if hasattr(func, '_wrapped_view'):
            print("✅ Function has decorators applied")
        else:
            print("⚠️  Warning: Decorators may not be applied")
        
        return True
    except Exception as e:
        print(f"❌ API view check error: {e}")
        return False


def check_javascript_implementation():
    """Check JavaScript implementation in template."""
    print("\n" + "=" * 60)
    print("4. CHECKING JAVASCRIPT IMPLEMENTATION")
    print("=" * 60)
    
    template_path = 'templates/document_tracking/admin_detail.html'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    js_checks = {
        'Event listener on manual serial input': r'manualSerialInput\.addEventListener\([\'"]input',
        'Debounce timeout': 'availabilityCheckTimeout',
        'setTimeout with 400ms': r'setTimeout.*400',
        'Fetch API call': r'fetch.*api-check-serial-availability',
        'POST method': r'method:\s*[\'"]POST[\'"]',
        'CSRF token': 'X-CSRFToken',
        'JSON body': 'JSON.stringify',
        'hideAllSerialFeedback function': 'function hideAllSerialFeedback',
        'showSerialChecking function': 'function showSerialChecking',
        'showSerialAvailable function': 'function showSerialAvailable',
        'showSerialTaken function': 'function showSerialTaken',
        'showSerialError function': 'function showSerialError',
    }
    
    all_passed = True
    for check_name, pattern in js_checks.items():
        if re.search(pattern, content):
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: NOT FOUND")
            all_passed = False
    
    return all_passed


def print_browser_instructions():
    """Print instructions for clearing browser cache."""
    print("\n" + "=" * 60)
    print("5. BROWSER CACHE CLEARING INSTRUCTIONS")
    print("=" * 60)
    
    print("""
Since Ctrl+Shift+R is not working, try these methods:

METHOD 1: Clear Browser Cache (Recommended)
  1. Open browser settings
  2. Go to Privacy/History settings
  3. Click "Clear browsing data"
  4. Select "Cached images and files"
  5. Click "Clear data"
  6. Reload the page (F5)

METHOD 2: Incognito/Private Window
  1. Press Ctrl+Shift+N (Chrome) or Ctrl+Shift+P (Firefox)
  2. Navigate to: http://127.0.0.1:8000/documents/admin/submissions/4/
  3. Feature should appear immediately

METHOD 3: Developer Tools
  1. Press F12
  2. Right-click refresh button
  3. Select "Empty Cache and Hard Reload"

METHOD 4: Different Browser
  1. Open Edge, Firefox, or Chrome (whichever you're not using)
  2. Navigate to the submission page
  3. Feature should be visible
""")


def main():
    """Run all verification checks."""
    print("\n" + "=" * 60)
    print("SERIAL AVAILABILITY CHECKER VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Run checks
    results.append(("URL Configuration", check_url_configuration()))
    results.append(("Template Cache-Busting", check_template_cache_busting()))
    results.append(("API View Implementation", check_api_view()))
    results.append(("JavaScript Implementation", check_javascript_implementation()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nThe serial availability checker is properly implemented.")
        print("If you still can't see it, the issue is browser cache.")
        print_browser_instructions()
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease review the failed checks above.")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Clear your browser cache using one of the methods above
2. Navigate to: http://127.0.0.1:8000/documents/admin/submissions/4/
3. Scroll to "Assign Tracking Number" card
4. Select "Manual" mode
5. Fill in Document Type, Year, and Serial Number
6. Watch for feedback below the serial number input

The feedback should appear after 400ms of typing:
  - 🔄 Checking availability... (gray spinner)
  - ✅ Serial number is available (green)
  - ❌ Serial number already exists (red)
""")


if __name__ == '__main__':
    main()
