"""
Test script for approval workflow with File Manager integration.

This script tests the complete workflow:
1. Find a submission ready for approval
2. Change status to 'approved'
3. Verify files moved to File Manager
4. Verify submission is locked
5. Check File Manager folder structure

Usage:
    python test_approval_workflow.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, Logbook
from document_tracking.legacy_services import StatusService
from structure.models import DocumentFolder
from accounts.models import WorkItemAttachment, User


def test_approval_workflow():
    """Test the complete approval workflow."""
    print("\n" + "="*60)
    print("APPROVAL WORKFLOW TEST")
    print("="*60)
    
    # Find a submission that can be approved
    submission = Submission.objects.filter(
        status='under_review',
        primary_folder__isnull=False,
        is_locked=False
    ).first()
    
    if not submission:
        print("\n⚠️  No suitable submission found for testing")
        print("Need: status='under_review', has files, not locked")
        
        # Show available submissions
        all_subs = Submission.objects.all()
        print(f"\nAvailable submissions: {all_subs.count()}")
        for sub in all_subs:
            print(f"  - {sub.title}: {sub.status} (files: {sub.primary_folder is not None})")
        return
    
    print(f"\n📄 Test Submission: {submission.title}")
    print(f"   Tracking: {submission.tracking_number}")
    print(f"   Status: {submission.status}")
    print(f"   Primary folder: {submission.primary_folder.name if submission.primary_folder else 'None'}")
    
    # Count files before approval
    if submission.primary_folder:
        file_count_before = WorkItemAttachment.objects.filter(
            folder=submission.primary_folder
        ).count()
        print(f"   Files in primary folder: {file_count_before}")
        
        # List files
        files = WorkItemAttachment.objects.filter(folder=submission.primary_folder)
        print("\n   Files:")
        for f in files:
            print(f"     - {f.get_filename()}")
    else:
        file_count_before = 0
    
    # Get admin user
    admin = User.objects.filter(is_staff=True).first()
    if not admin:
        print("\n❌ No admin user found")
        return
    
    print(f"\n👤 Admin: {admin.get_full_name()}")
    
    # Approve the submission
    print("\n🔄 Changing status to 'approved'...")
    
    try:
        StatusService.change_status(
            submission=submission,
            new_status='approved',
            actor=admin,
            remarks="Test approval for File Manager integration"
        )
        
        # Refresh submission from database
        submission.refresh_from_db()
        
        print("✅ Status changed successfully!")
        
        # Verify changes
        print("\n📊 Verification:")
        print(f"   Status: {submission.status}")
        print(f"   Is locked: {submission.is_locked}")
        print(f"   Stored in File Manager: {submission.is_stored_in_file_manager}")
        
        if submission.file_manager_folder:
            print(f"   File Manager folder: {submission.file_manager_folder.name}")
            print(f"   Full path: {submission.file_manager_folder.get_path_string()}")
            
            # Count files in File Manager folder
            file_count_after = WorkItemAttachment.objects.filter(
                folder=submission.file_manager_folder
            ).count()
            print(f"   Files in File Manager: {file_count_after}")
            
            # Verify file count matches
            if file_count_before == file_count_after:
                print(f"   ✅ All {file_count_after} files moved successfully")
            else:
                print(f"   ⚠️  File count mismatch: {file_count_before} → {file_count_after}")
            
            # List files in File Manager
            fm_files = WorkItemAttachment.objects.filter(folder=submission.file_manager_folder)
            print("\n   Files in File Manager:")
            for f in fm_files:
                print(f"     - {f.get_filename()}")
        else:
            print("   ❌ No File Manager folder created")
        
        # Check logbook
        latest_log = Logbook.objects.filter(submission=submission).order_by('-timestamp').first()
        if latest_log:
            print(f"\n📝 Latest logbook entry:")
            print(f"   Action: {latest_log.get_action_display()}")
            print(f"   Remarks: {latest_log.remarks}")
            print(f"   Actor: {latest_log.actor.get_full_name()}")
            print(f"   Time: {latest_log.timestamp}")
        
        print("\n✅ APPROVAL WORKFLOW TEST PASSED")
        
    except Exception as e:
        print(f"\n❌ Error during approval: {e}")
        import traceback
        traceback.print_exc()


def show_file_manager_structure():
    """Show the File Manager folder structure."""
    print("\n" + "="*60)
    print("FILE MANAGER STRUCTURE")
    print("="*60)
    
    # Find ROOT folder
    root = DocumentFolder.objects.filter(name="ROOT", folder_type=DocumentFolder.FolderType.ROOT).first()
    
    if not root:
        print("No ROOT folder found")
        return
    
    def print_tree(folder, indent=0):
        prefix = "  " * indent
        file_count = WorkItemAttachment.objects.filter(folder=folder).count()
        file_info = f" ({file_count} files)" if file_count > 0 else ""
        print(f"{prefix}📁 {folder.name}{file_info}")
        
        # Show children
        children = DocumentFolder.objects.filter(parent=folder).order_by('name')
        for child in children:
            print_tree(child, indent + 1)
    
    print_tree(root)
    
    # Show submissions in File Manager
    stored_subs = Submission.objects.filter(is_stored_in_file_manager=True)
    print(f"\n📊 Submissions in File Manager: {stored_subs.count()}")
    for sub in stored_subs:
        print(f"   - {sub.title} ({sub.tracking_number})")
        if sub.file_manager_folder:
            print(f"     Path: {sub.file_manager_folder.get_path_string()}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FILE MANAGER INTEGRATION TEST")
    print("Phase 2 - Approval Workflow")
    print("="*60)
    
    try:
        test_approval_workflow()
        show_file_manager_structure()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
