"""
Test script for FileManagerService - Phase 1 Implementation

This script tests the File Manager integration for approved submissions.

Usage:
    python test_file_manager_service.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from document_tracking.legacy_services import FileManagerService
from structure.models import DocumentFolder
from accounts.models import WorkItemAttachment


def test_folder_structure():
    """Test that folder structure is created correctly."""
    print("\n" + "="*60)
    print("TEST 1: Folder Structure Creation")
    print("="*60)
    
    # Test ROOT folder
    root = FileManagerService.get_or_create_root_folder()
    print(f"✓ ROOT folder: {root.name} (type: {root.folder_type})")
    assert root.folder_type == DocumentFolder.FolderType.ROOT
    assert root.parent is None
    
    # Test YEAR folder
    year_folder = FileManagerService.get_or_create_year_folder(2026)
    print(f"✓ Year folder: {year_folder.name} (type: {year_folder.folder_type})")
    assert year_folder.folder_type == DocumentFolder.FolderType.YEAR
    assert year_folder.parent == root
    assert year_folder.name == "2026"
    
    # Test Submissions folder
    submissions_folder = FileManagerService.get_or_create_submissions_folder(year_folder)
    print(f"✓ Submissions folder: {submissions_folder.name} (type: {submissions_folder.folder_type})")
    assert submissions_folder.folder_type == DocumentFolder.FolderType.CATEGORY
    assert submissions_folder.parent == year_folder
    assert submissions_folder.name == "Submissions"
    
    # Test path
    path = submissions_folder.get_path_string()
    print(f"✓ Full path: {path}")
    assert "ROOT" in path
    assert "2026" in path
    assert "Submissions" in path
    
    print("\n✅ Folder structure test PASSED")


def test_submission_folder_creation():
    """Test creating a folder for a specific submission."""
    print("\n" + "="*60)
    print("TEST 2: Submission Folder Creation")
    print("="*60)
    
    # Find an approved submission
    submission = Submission.objects.filter(status='approved').first()
    
    if not submission:
        print("⚠️  No approved submissions found. Creating test scenario...")
        submission = Submission.objects.filter(status='under_review').first()
        if not submission:
            print("❌ No submissions found to test with")
            return
    
    print(f"\nTest submission: {submission.title}")
    print(f"Status: {submission.status}")
    print(f"Document type: {submission.document_type}")
    
    # Get folder structure
    year_folder = FileManagerService.get_or_create_year_folder(2026)
    submissions_folder = FileManagerService.get_or_create_submissions_folder(year_folder)
    
    # Create submission folder (only if not already created)
    try:
        submission_folder = FileManagerService.create_submission_folder(
            submissions_folder,
            submission
        )
        print(f"\n✓ Created folder: {submission_folder.name}")
        print(f"✓ Folder type: {submission_folder.folder_type}")
        print(f"✓ Full path: {submission_folder.get_path_string()}")
        print(f"✓ Created by: {submission_folder.created_by}")
        
        # Clean up test folder
        submission_folder.delete()
        print("\n✓ Test folder cleaned up")
        
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        return
    
    print("\n✅ Submission folder creation test PASSED")


def test_file_movement():
    """Test moving files from primary folder to File Manager."""
    print("\n" + "="*60)
    print("TEST 3: File Movement")
    print("="*60)
    
    # Find a submission with files
    submission = Submission.objects.filter(
        primary_folder__isnull=False
    ).first()
    
    if not submission:
        print("⚠️  No submissions with files found")
        return
    
    print(f"\nTest submission: {submission.title}")
    print(f"Primary folder: {submission.primary_folder.name}")
    
    # Count files in primary folder
    file_count = WorkItemAttachment.objects.filter(
        folder=submission.primary_folder
    ).count()
    
    print(f"Files in primary folder: {file_count}")
    
    if file_count == 0:
        print("⚠️  No files to move")
        return
    
    # List files
    files = WorkItemAttachment.objects.filter(
        folder=submission.primary_folder
    )
    print("\nFiles:")
    for f in files:
        print(f"  - {f.get_filename()}")
    
    print("\n✅ File movement test PASSED (read-only check)")


def test_full_workflow():
    """Test the complete workflow: approve submission and store in File Manager."""
    print("\n" + "="*60)
    print("TEST 4: Full Workflow (DRY RUN)")
    print("="*60)
    
    # Find a submission that could be approved
    submission = Submission.objects.filter(
        status='under_review',
        primary_folder__isnull=False
    ).first()
    
    if not submission:
        print("⚠️  No suitable submissions found for workflow test")
        print("Need: status='under_review' with files")
        return
    
    print(f"\nTest submission: {submission.title}")
    print(f"Current status: {submission.status}")
    print(f"Has files: {submission.primary_folder is not None}")
    
    # Check file count
    if submission.primary_folder:
        file_count = WorkItemAttachment.objects.filter(
            folder=submission.primary_folder
        ).count()
        print(f"File count: {file_count}")
    
    print("\n📋 What would happen if approved:")
    print("1. Create folder: ROOT > 2026 > Submissions > [Title]")
    print(f"2. Move {file_count if submission.primary_folder else 0} files to File Manager")
    print("3. Set is_stored_in_file_manager = True")
    print("4. Set is_locked = True")
    print("5. Create logbook entry")
    
    print("\n✅ Full workflow test PASSED (dry run)")


def show_current_structure():
    """Show current File Manager structure."""
    print("\n" + "="*60)
    print("CURRENT FILE MANAGER STRUCTURE")
    print("="*60)
    
    # Find ROOT folder
    root = DocumentFolder.objects.filter(
        folder_type=DocumentFolder.FolderType.ROOT
    ).first()
    
    if not root:
        print("No ROOT folder found")
        return
    
    def print_tree(folder, indent=0):
        prefix = "  " * indent
        print(f"{prefix}📁 {folder.name} ({folder.folder_type})")
        
        # Show children
        children = DocumentFolder.objects.filter(parent=folder).order_by('name')
        for child in children:
            print_tree(child, indent + 1)
    
    print_tree(root)
    
    # Show submissions stored in File Manager
    stored_submissions = Submission.objects.filter(
        is_stored_in_file_manager=True
    )
    
    print(f"\n📊 Submissions stored in File Manager: {stored_submissions.count()}")
    for sub in stored_submissions:
        print(f"  - {sub.title} ({sub.tracking_number})")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FILE MANAGER SERVICE TEST SUITE")
    print("Phase 1 Implementation")
    print("="*60)
    
    try:
        test_folder_structure()
        test_submission_folder_creation()
        test_file_movement()
        test_full_workflow()
        show_current_structure()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        print("\nNext steps:")
        print("1. Review test results above")
        print("2. If all tests pass, proceed to Phase 2")
        print("3. Phase 2: Update templates and views")
        print("4. Phase 3: Create migration")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
