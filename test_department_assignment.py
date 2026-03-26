"""
Test script for department-based storage implementation.

This script tests:
1. Section CRUD operations
2. Department assignment to submissions
3. Validation before approval
4. Storage path generation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
django.setup()

from document_tracking.models import Section, Submission
from document_tracking.services.section_service import (
    get_all_sections,
    get_active_sections,
    get_section_stats,
    can_delete_section,
)
from document_tracking.legacy_services import StatusService
from accounts.models import User


def test_sections():
    """Test section operations."""
    print("\n" + "="*60)
    print("TEST 1: Section Operations")
    print("="*60)
    
    # Get all sections
    sections = get_all_sections()
    print(f"\n✓ Total sections: {sections.count()}")
    
    for section in sections:
        print(f"\n  Section: {section.display_name}")
        print(f"    - Name: {section.name}")
        print(f"    - Active: {section.is_active}")
        print(f"    - Order: {section.order}")
        print(f"    - Description: {section.description}")
        
        # Get stats
        stats = get_section_stats(section.id)
        print(f"    - Total Submissions: {stats['total_submissions']}")
        print(f"    - Pending: {stats['pending_submissions']}")
        print(f"    - Approved: {stats['approved_submissions']}")
        print(f"    - Officers: {stats['officers_count']}")
        
        # Check if can delete
        can_delete = can_delete_section(section.id)
        print(f"    - Can Delete: {can_delete}")
    
    # Get active sections only
    active_sections = get_active_sections()
    print(f"\n✓ Active sections: {active_sections.count()}")


def test_department_assignment():
    """Test department assignment to submissions."""
    print("\n" + "="*60)
    print("TEST 2: Department Assignment")
    print("="*60)
    
    # Get a submission without assigned section
    submission = Submission.objects.filter(
        tracking_number__isnull=False,
        assigned_section__isnull=True
    ).first()
    
    if not submission:
        print("\n⚠ No submissions found without assigned section")
        print("  Creating test scenario...")
        
        # Get any submission with tracking number
        submission = Submission.objects.filter(
            tracking_number__isnull=False
        ).first()
        
        if submission:
            # Clear assigned section for testing
            submission.assigned_section = None
            submission.save()
            print(f"✓ Cleared section from submission #{submission.id}")
    
    if submission:
        print(f"\n✓ Testing with submission #{submission.id}")
        print(f"  - Title: {submission.title}")
        print(f"  - Tracking: {submission.tracking_number}")
        print(f"  - Status: {submission.status}")
        print(f"  - Assigned Section: {submission.assigned_section}")
        
        # Get first active section
        section = Section.objects.filter(is_active=True).first()
        
        if section:
            print(f"\n✓ Assigning section: {section.display_name}")
            submission.assigned_section = section
            submission.save()
            
            print(f"✓ Section assigned successfully!")
            print(f"  - Storage path will be: ROOT / 2026 / Submissions / {section.display_name} / {submission.title}")
        else:
            print("\n❌ No active sections found")
    else:
        print("\n⚠ No submissions found for testing")


def test_approval_validation():
    """Test validation before approval."""
    print("\n" + "="*60)
    print("TEST 3: Approval Validation")
    print("="*60)
    
    # Get a submission without assigned section
    submission = Submission.objects.filter(
        tracking_number__isnull=False,
        assigned_section__isnull=True,
        status__in=['received', 'under_review']
    ).first()
    
    if not submission:
        print("\n⚠ No submissions found for validation test")
        return
    
    print(f"\n✓ Testing with submission #{submission.id}")
    print(f"  - Title: {submission.title}")
    print(f"  - Tracking: {submission.tracking_number}")
    print(f"  - Status: {submission.status}")
    print(f"  - Assigned Section: {submission.assigned_section}")
    
    # Get admin user
    admin = User.objects.filter(is_staff=True).first()
    
    if not admin:
        print("\n❌ No admin user found")
        return
    
    # Try to approve without section (should fail)
    print("\n✓ Attempting to approve without assigned section...")
    try:
        StatusService.change_status(
            submission=submission,
            new_status='approved',
            actor=admin,
            remarks='Test approval'
        )
        print("❌ FAIL: Approval succeeded without section (should have failed)")
    except ValueError as e:
        print(f"✓ PASS: Approval blocked as expected")
        print(f"  Error: {str(e)}")
    
    # Assign section and try again
    section = Section.objects.filter(is_active=True).first()
    if section:
        print(f"\n✓ Assigning section: {section.display_name}")
        submission.assigned_section = section
        submission.save()
        
        print("✓ Attempting to approve with assigned section...")
        try:
            # Note: This might still fail if workflow doesn't allow direct approval
            # from current status, but it should NOT fail due to missing section
            StatusService.change_status(
                submission=submission,
                new_status='approved',
                actor=admin,
                remarks='Test approval with section'
            )
            print("✓ PASS: Approval succeeded with section assigned")
        except ValueError as e:
            if 'department assignment' in str(e).lower():
                print(f"❌ FAIL: Still blocked by section validation: {str(e)}")
            else:
                print(f"✓ PASS: Blocked by workflow (not section): {str(e)}")


def test_storage_path():
    """Test storage path generation."""
    print("\n" + "="*60)
    print("TEST 4: Storage Path Generation")
    print("="*60)
    
    # Get submissions with assigned sections
    submissions = Submission.objects.filter(
        assigned_section__isnull=False
    )[:5]
    
    if not submissions:
        print("\n⚠ No submissions with assigned sections found")
        return
    
    print(f"\n✓ Found {submissions.count()} submissions with assigned sections")
    
    for submission in submissions:
        print(f"\n  Submission #{submission.id}: {submission.title}")
        print(f"    - Section: {submission.assigned_section.display_name}")
        print(f"    - Status: {submission.status}")
        
        # Generate storage path
        from datetime import datetime
        year = datetime.now().year
        storage_path = f"ROOT / {year} / Submissions / {submission.assigned_section.display_name} / {submission.title}"
        print(f"    - Storage Path: {storage_path}")
        
        if submission.file_manager_folder:
            actual_path = submission.file_manager_folder.get_path_string()
            print(f"    - Actual Path: {actual_path}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("DEPARTMENT-BASED STORAGE TEST SUITE")
    print("="*60)
    
    try:
        test_sections()
        test_department_assignment()
        test_approval_validation()
        test_storage_path()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60)
        print("\nNext steps:")
        print("1. Run migrations: python manage.py makemigrations")
        print("2. Apply migrations: python manage.py migrate")
        print("3. Create default sections: python manage.py create_default_sections")
        print("4. Test in browser:")
        print("   - Go to Settings > Sections")
        print("   - View a submission without assigned section")
        print("   - Assign a section")
        print("   - Try to approve (should work)")
        print("   - Verify storage path in File Manager")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
