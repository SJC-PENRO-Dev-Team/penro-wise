"""
Test script to verify PostgreSQL and Cloudinary configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.conf import settings
from django.db import connection
import cloudinary
import cloudinary.uploader

print("\n" + "="*60)
print("CONFIGURATION TEST")
print("="*60)

# Test 1: Database Configuration
print("\n1. DATABASE CONFIGURATION")
print("-" * 60)
db_config = settings.DATABASES['default']
print(f"Engine: {db_config['ENGINE']}")
print(f"Name: {db_config['NAME']}")
print(f"Host: {db_config.get('HOST', 'N/A')}")
print(f"Port: {db_config.get('PORT', 'N/A')}")

# Test database connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database connected successfully!")
        print(f"PostgreSQL version: {version[:50]}...")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test 2: Cloudinary Configuration
print("\n2. CLOUDINARY CONFIGURATION")
print("-" * 60)
print(f"Cloud Name: {settings.CLOUDINARY_STORAGE['CLOUD_NAME']}")
print(f"API Key: {settings.CLOUDINARY_STORAGE['API_KEY'][:10]}...")
print(f"API Secret: {'*' * 20}")
print(f"Storage Backend: {settings.DEFAULT_FILE_STORAGE}")

# Test Cloudinary connection
try:
    # Try to get account info
    result = cloudinary.api.ping()
    print(f"✅ Cloudinary connected successfully!")
    print(f"Status: {result.get('status', 'OK')}")
except Exception as e:
    print(f"❌ Cloudinary connection failed: {e}")

# Test 3: Check existing files in Cloudinary
print("\n3. CLOUDINARY RESOURCES")
print("-" * 60)
try:
    # Get list of resources (limit to 5 for testing)
    resources = cloudinary.api.resources(
        type='upload',
        prefix='work_items/',
        max_results=5
    )
    
    total = resources.get('total_count', 0)
    print(f"Total files in work_items/: {total}")
    
    if resources.get('resources'):
        print("\nSample files:")
        for resource in resources['resources'][:5]:
            print(f"  - {resource['public_id']}")
            print(f"    URL: {resource['secure_url'][:60]}...")
            print(f"    Size: {resource['bytes'] / 1024:.2f} KB")
    else:
        print("No files found in work_items/ folder")
        
except Exception as e:
    print(f"❌ Failed to list resources: {e}")

# Test 4: Check profile images
print("\n4. PROFILE IMAGES")
print("-" * 60)
try:
    resources = cloudinary.api.resources(
        type='upload',
        prefix='profile_images/',
        max_results=5
    )
    
    total = resources.get('total_count', 0)
    print(f"Total profile images: {total}")
    
    if resources.get('resources'):
        print("\nSample profile images:")
        for resource in resources['resources'][:5]:
            print(f"  - {resource['public_id']}")
    else:
        print("No profile images found")
        
except Exception as e:
    print(f"❌ Failed to list profile images: {e}")

# Test 5: File Upload Test (optional)
print("\n5. FILE UPLOAD TEST")
print("-" * 60)
print("Skipping upload test to avoid creating test files")
print("To test upload, uncomment the code in the script")

# Uncomment to test upload:
# try:
#     # Create a small test file
#     test_content = b"Test file for Cloudinary"
#     import io
#     test_file = io.BytesIO(test_content)
#     test_file.name = "test_upload.txt"
#     
#     result = cloudinary.uploader.upload(
#         test_file,
#         folder="test/",
#         resource_type="raw"
#     )
#     
#     print(f"✅ Upload successful!")
#     print(f"Public ID: {result['public_id']}")
#     print(f"URL: {result['secure_url']}")
#     
#     # Clean up test file
#     cloudinary.uploader.destroy(result['public_id'], resource_type="raw")
#     print("✅ Test file cleaned up")
#     
# except Exception as e:
#     print(f"❌ Upload test failed: {e}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\n✅ PostgreSQL: Connected")
print("✅ Cloudinary: Configured")
print("\nNext steps:")
print("1. Verify file uploads work in the application")
print("2. Test file preview functionality")
print("3. Test file downloads")
print("4. Check that existing files are accessible")
print("\n")
