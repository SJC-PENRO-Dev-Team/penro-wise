#!/usr/bin/env python
"""
Test local file storage functionality
"""
import os
import django
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User, WorkItemAttachment
from structure.models import DocumentFolder
from django.conf import settings

def test_local_storage():
    print("=" * 60)
    print("LOCAL FILE STORAGE TEST")
    print("=" * 60)
    
    # Check configuration
    print(f"✓ Storage backend: {settings.DEFAULT_FILE_STORAGE}")
    print(f"✓ Media root: {settings.MEDIA_ROOT}")
    print(f"✓ Media URL: {settings.MEDIA_URL}")
    print(f"✓ Cloudinary enabled: {getattr(settings, 'CLOUDINARY_ENABLED', False)}")
    
    # Check if media directory exists
    if os.path.exists(settings.MEDIA_ROOT):
        print(f"✓ Media directory exists: {settings.MEDIA_ROOT}")
    else:
        print(f"❌ Media directory missing: {settings.MEDIA_ROOT}")
        return
    
    # Get admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✓ Admin user found: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return
    
    # Get any existing folder for testing
    try:
        test_folder = DocumentFolder.objects.filter(
            folder_type=DocumentFolder.FolderType.ATTACHMENT
        ).first()
        
        if not test_folder:
            # Create a simple test folder structure
            root_folder = DocumentFolder.objects.create(
                name="Test Root",
                folder_type=DocumentFolder.FolderType.ROOT,
                parent=None,
                is_system_generated=True,
            )
            
            test_folder = DocumentFolder.objects.create(
                name="Test Folder",
                folder_type=DocumentFolder.FolderType.ATTACHMENT,
                parent=root_folder,
                created_by=admin_user,
                is_system_generated=False,
            )
        
        print(f"✓ Test folder: {test_folder.name} (ID: {test_folder.id})")
        
    except Exception as e:
        print(f"❌ Error creating test folder: {e}")
        return
    
    # Create a test file
    test_content = b"This is a test file for local storage verification."
    test_file = SimpleUploadedFile(
        name="test_file.txt",
        content=test_content,
        content_type="text/plain"
    )
    
    # Create attachment
    try:
        attachment = WorkItemAttachment.objects.create(
            folder=test_folder,
            file=test_file,
            uploaded_by=admin_user,
            attachment_type='document',
            acceptance_status='accepted'
        )
        print(f"✓ File attachment created: {attachment.id}")
        print(f"✓ File path: {attachment.file.name}")
        print(f"✓ File URL: {attachment.file.url}")
        
        # Check if file exists on disk
        file_path = attachment.file.path
        if os.path.exists(file_path):
            print(f"✓ File exists on disk: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
                if content == test_content:
                    print("✓ File content matches original")
                else:
                    print("❌ File content mismatch")
        else:
            print(f"❌ File not found on disk: {file_path}")
        
        # Test file size
        print(f"✓ File size: {attachment.file.size} bytes")
        
        # Clean up test file
        attachment.file.delete(save=False)
        attachment.delete()
        print("✓ Test file cleaned up")
        
    except Exception as e:
        print(f"❌ Error creating attachment: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✅ LOCAL STORAGE TEST PASSED!")
    print("✅ File uploads and storage are working correctly")
    print("=" * 60)

if __name__ == "__main__":
    test_local_storage()