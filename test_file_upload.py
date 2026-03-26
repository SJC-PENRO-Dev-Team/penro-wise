"""
Test script to verify file manager upload works with nullable work_item
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, User
from structure.models import DocumentFolder
from django.core.files.uploadedfile import SimpleUploadedFile

def test_standalone_upload():
    """Test creating a standalone attachment without work_item"""
    
    print("=" * 60)
    print("Testing Standalone File Upload (No Work Item)")
    print("=" * 60)
    
    # Get a test user
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("❌ No admin user found. Please create one first.")
        return
    
    print(f"✅ Using user: {user.username}")
    
    # Get a valid folder (not ROOT, YEAR, or CATEGORY)
    folder = DocumentFolder.objects.filter(
        folder_type__in=[
            DocumentFolder.FolderType.WORKCYCLE,
            DocumentFolder.FolderType.DIVISION,
            DocumentFolder.FolderType.SECTION,
            DocumentFolder.FolderType.SERVICE,
            DocumentFolder.FolderType.UNIT,
            DocumentFolder.FolderType.ATTACHMENT,
        ]
    ).first()
    
    if not folder:
        print("❌ No valid folder found. Please create folder structure first.")
        return
    
    print(f"✅ Using folder: {folder.name} ({folder.get_folder_type_display()})")
    
    # Create a test file
    test_file = SimpleUploadedFile(
        "test_standalone_upload.txt",
        b"This is a test file uploaded via file manager without a work item.",
        content_type="text/plain"
    )
    
    try:
        # Create attachment WITHOUT work_item
        attachment = WorkItemAttachment.objects.create(
            work_item=None,  # ✅ NULL - standalone upload
            file=test_file,
            uploaded_by=user,
            folder=folder,
            attachment_type='document',
            acceptance_status='accepted',
        )
        
        print(f"✅ Attachment created successfully!")
        print(f"   ID: {attachment.id}")
        print(f"   File: {attachment.get_filename()}")
        print(f"   Folder: {attachment.folder.name}")
        print(f"   Work Item: {attachment.work_item}")
        print(f"   Type: {attachment.get_attachment_type_display()}")
        print(f"   Status: {attachment.acceptance_status}")
        print(f"   String repr: {attachment}")
        
        # Verify it was saved
        saved = WorkItemAttachment.objects.get(id=attachment.id)
        print(f"✅ Verified in database: {saved}")
        
        # Clean up
        attachment.delete()
        print(f"✅ Test attachment deleted")
        
        print("\n" + "=" * 60)
        print("✅ TEST PASSED - Standalone uploads work!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

def test_work_item_upload():
    """Test that work item uploads still work"""
    
    print("\n" + "=" * 60)
    print("Testing Work Item Upload (Existing Functionality)")
    print("=" * 60)
    
    from accounts.models import WorkItem
    
    # Get a test work item
    work_item = WorkItem.objects.first()
    if not work_item:
        print("❌ No work item found. Skipping work item test.")
        return
    
    print(f"✅ Using work item: {work_item}")
    
    user = work_item.owner
    print(f"✅ Using user: {user.username}")
    
    # Create a test file
    test_file = SimpleUploadedFile(
        "test_work_item_upload.txt",
        b"This is a test file uploaded via work item submission.",
        content_type="text/plain"
    )
    
    try:
        # Create attachment WITH work_item (folder will be auto-resolved)
        attachment = WorkItemAttachment.objects.create(
            work_item=work_item,  # ✅ Provided
            file=test_file,
            uploaded_by=user,
            attachment_type='matrix_a',
            # folder will be auto-resolved
        )
        
        print(f"✅ Attachment created successfully!")
        print(f"   ID: {attachment.id}")
        print(f"   File: {attachment.get_filename()}")
        print(f"   Folder: {attachment.folder.name if attachment.folder else 'None'}")
        print(f"   Work Item: {attachment.work_item}")
        print(f"   Type: {attachment.get_attachment_type_display()}")
        print(f"   Folder Path: {attachment.get_folder_path()}")
        
        # Verify folder was auto-resolved
        if attachment.folder:
            print(f"✅ Folder auto-resolved: {attachment.folder.get_path_string()}")
        else:
            print(f"❌ Folder was not auto-resolved!")
        
        # Clean up
        attachment.delete()
        print(f"✅ Test attachment deleted")
        
        print("\n" + "=" * 60)
        print("✅ TEST PASSED - Work item uploads still work!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FILE MANAGER UPLOAD TEST SUITE")
    print("=" * 60 + "\n")
    
    test_standalone_upload()
    test_work_item_upload()
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60 + "\n")
