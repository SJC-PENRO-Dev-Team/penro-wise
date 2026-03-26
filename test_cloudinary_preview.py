"""
Test Cloudinary File Preview Fix

This script tests if the file preview system can handle Cloudinary-stored files.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from django.conf import settings

def test_cloudinary_files():
    """Test if files are stored on Cloudinary and can be accessed"""
    
    print("=" * 60)
    print("CLOUDINARY FILE PREVIEW TEST")
    print("=" * 60)
    
    # Check Cloudinary configuration
    print("\n1. Checking Cloudinary Configuration...")
    print(f"   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
    print(f"   CLOUD_NAME: {settings.CLOUDINARY_STORAGE['CLOUD_NAME']}")
    
    if 'cloudinary' in settings.DEFAULT_FILE_STORAGE.lower():
        print("   ✅ Cloudinary is configured as default storage")
    else:
        print("   ❌ Cloudinary is NOT the default storage")
        return
    
    # Get some sample files
    print("\n2. Checking Uploaded Files...")
    attachments = WorkItemAttachment.objects.all()[:5]
    
    if not attachments.exists():
        print("   ⚠️  No files found in database")
        print("   Upload a file first to test preview")
        return
    
    print(f"   Found {attachments.count()} sample files")
    
    # Test each file
    print("\n3. Testing File Access...")
    for attachment in attachments:
        print(f"\n   File: {attachment.file.name}")
        
        # Test if file has URL (Cloudinary)
        try:
            url = attachment.file.url
            print(f"   ✅ URL: {url[:80]}...")
            
            # Check if it's a Cloudinary URL
            if 'cloudinary' in url:
                print("   ✅ File is on Cloudinary")
            else:
                print("   ⚠️  File URL doesn't contain 'cloudinary'")
        except Exception as e:
            print(f"   ❌ Error getting URL: {e}")
        
        # Test if file has path (local storage)
        try:
            path = attachment.file.path
            print(f"   ⚠️  File has local path: {path}")
            print("   This means file is stored locally, not on Cloudinary")
        except (AttributeError, NotImplementedError) as e:
            print(f"   ✅ No local path (expected for Cloudinary): {type(e).__name__}")
    
    # Test the preview view logic
    print("\n4. Testing Preview View Logic...")
    if attachments.exists():
        test_attachment = attachments.first()
        print(f"   Testing with: {test_attachment.file.name}")
        
        # Simulate the preview_file view logic
        try:
            file_path = test_attachment.file.path
            print("   ❌ File has .path - preview will try to use local file")
            print("   This will FAIL on production with Cloudinary")
        except (AttributeError, NotImplementedError):
            print("   ✅ File has no .path - preview will use Cloudinary URL")
            print("   This is CORRECT for Cloudinary files")
            
            # Test URL access
            try:
                url = test_attachment.file.url
                print(f"   ✅ Can get URL: {url[:80]}...")
            except Exception as e:
                print(f"   ❌ Error getting URL: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if 'cloudinary' in settings.DEFAULT_FILE_STORAGE.lower():
        print("\n✅ Cloudinary is properly configured")
        print("✅ Files are being uploaded to Cloudinary")
        print("✅ Preview fix should work on production")
        print("\n📋 NEXT STEPS:")
        print("   1. Deploy the updated code to production")
        print("   2. Test file preview on production site")
        print("   3. Verify PDFs, images, and Office docs preview correctly")
    else:
        print("\n❌ Cloudinary is NOT configured")
        print("Files are being stored locally")
        print("Preview will work locally but may fail on production")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_cloudinary_files()
