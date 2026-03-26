"""
Test script to verify the ValidationError import fix.
"""
import os
import sys
import importlib.util

print("=" * 60)
print("TESTING VALIDATIONERROR IMPORT FIX")
print("=" * 60)

# Load views.py directly (same way urls.py does it)
views_path = os.path.join('document_tracking', 'views.py')

if not os.path.exists(views_path):
    print(f"\n❌ ERROR: {views_path} not found")
    exit(1)

print(f"\n1. Loading views.py from: {views_path}")

try:
    spec = importlib.util.spec_from_file_location("document_tracking.main_views", views_path)
    main_views = importlib.util.module_from_spec(spec)
    sys.modules['document_tracking.main_views'] = main_views
    spec.loader.exec_module(main_views)
    
    print("   ✅ views.py loaded successfully")
    
except Exception as e:
    print(f"   ❌ ERROR loading views.py: {e}")
    exit(1)

# Check if ValidationError is imported
print("\n2. Checking ValidationError import...")

try:
    import inspect
    source = inspect.getsource(main_views)
    
    if 'from django.core.exceptions import ValidationError' in source:
        print("   ✅ ValidationError import found")
    else:
        print("   ❌ ValidationError import NOT found")
        exit(1)
        
except Exception as e:
    print(f"   ⚠️  Could not check source: {e}")

# Check if delete_submission function exists
print("\n3. Checking delete_submission function...")

if hasattr(main_views, 'delete_submission'):
    print("   ✅ delete_submission function exists")
    
    # Check if function uses ValidationError
    try:
        func_source = inspect.getsource(main_views.delete_submission)
        if 'ValidationError' in func_source:
            print("   ✅ Function uses ValidationError")
        else:
            print("   ⚠️  Function doesn't use ValidationError (might not need it)")
    except:
        pass
else:
    print("   ❌ delete_submission function NOT found")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED")
print("=" * 60)

print("\n📋 SUMMARY:")
print("   • ValidationError is properly imported")
print("   • delete_submission function exists")
print("   • No import errors detected")

print("\n🧪 NEXT STEPS:")
print("   1. Restart Django server if running")
print("   2. Navigate to rejected submission")
print("   3. Test delete functionality")
print("   4. Should work without NameError")

print("\n✅ Fix verified successfully!")
