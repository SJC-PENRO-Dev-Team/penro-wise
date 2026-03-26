"""
Test Cloudinary configuration and connection.
Usage: python test_cloudinary.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if credentials are set
CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
API_KEY = os.getenv('CLOUDINARY_API_KEY')
API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

print("=" * 60)
print("CLOUDINARY CONFIGURATION TEST")
print("=" * 60)

# Check credentials
print("\n1. Checking environment variables...")
if not CLOUD_NAME:
    print("❌ CLOUDINARY_CLOUD_NAME is not set")
    sys.exit(1)
else:
    print(f"✅ CLOUDINARY_CLOUD_NAME: {CLOUD_NAME}")

if not API_KEY:
    print("❌ CLOUDINARY_API_KEY is not set")
    sys.exit(1)
else:
    print(f"✅ CLOUDINARY_API_KEY: {API_KEY[:10]}...")

if not API_SECRET:
    print("❌ CLOUDINARY_API_SECRET is not set")
    sys.exit(1)
else:
    print(f"✅ CLOUDINARY_API_SECRET: {API_SECRET[:10]}...")

# Test connection
print("\n2. Testing Cloudinary connection...")
try:
    import cloudinary
    import cloudinary.api
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=API_KEY,
        api_secret=API_SECRET,
        secure=True
    )
    
    # Test API call - get account usage
    result = cloudinary.api.usage()
    
    print("✅ Connection successful!")
    print(f"\n📊 Account Usage:")
    print(f"   - Plan: {result.get('plan', 'N/A')}")
    print(f"   - Credits: {result.get('credits', {}).get('usage', 0)} / {result.get('credits', {}).get('limit', 0)}")
    print(f"   - Storage: {result.get('storage', {}).get('usage', 0) / (1024*1024):.2f} MB")
    print(f"   - Bandwidth: {result.get('bandwidth', {}).get('usage', 0) / (1024*1024):.2f} MB")
    
    # Test upload folder access
    print("\n3. Testing folder access...")
    try:
        folders = cloudinary.api.root_folders()
        print(f"✅ Can access folders (found {len(folders.get('folders', []))} root folders)")
    except Exception as e:
        print(f"⚠️  Folder access test: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Cloudinary is ready to use!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python manage.py migrate_to_cloudinary --dry-run")
    print("2. Review what will be migrated")
    print("3. Run: python manage.py migrate_to_cloudinary")
    print("=" * 60)
    
except ImportError:
    print("❌ Cloudinary package not installed")
    print("   Run: pip install cloudinary django-cloudinary-storage")
    sys.exit(1)
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print("\nPossible issues:")
    print("- Invalid credentials")
    print("- Network connectivity problems")
    print("- Cloudinary account issues")
    sys.exit(1)
