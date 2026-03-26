"""
Test script to verify tracking number assignment modes work correctly.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission
from document_tracking.legacy_services import TrackingService
from accounts.models import User

def test_tracking_modes():
    print("=" * 60)
    print("TESTING TRACKING NUMBER ASSIGNMENT MODES")
    print("=" * 60)
    
    # Get a test user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    print(f"\n✓ Using test user: {user.email}")
    
    # Find submissions without tracking numbers
    pending_submissions = Submission.objects.filter(
        tracking_number__isnull=True
    ).order_by('id')
    
    print(f"\n✓ Found {pending_submissions.count()} submissions without tracking numbers")
    
    if pending_submissions.count() < 2:
        print("⚠ Need at least 2 submissions to test both modes")
        return
    
    # Test Mode A (Auto-generate)
    print("\n" + "=" * 60)
    print("TEST 1: Mode A - Auto-Generate")
    print("=" * 60)
    
    submission1 = pending_submissions[0]
    print(f"\nSubmission ID: {submission1.id}")
    print(f"Title: {submission1.title}")
    print(f"Current tracking number: {submission1.tracking_number}")
    
    try:
        TrackingService.assign_tracking_number(
            submission=submission1,
            mode='auto',
            actor=user
        )
        submission1.refresh_from_db()
        print(f"✓ Auto-generated tracking number: {submission1.tracking_number}")
        print(f"✓ Status changed to: {submission1.status}")
        print(f"✓ Tracking locked: {submission1.tracking_locked}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Mode B (Manual)
    print("\n" + "=" * 60)
    print("TEST 2: Mode B - Manual Entry")
    print("=" * 60)
    
    if pending_submissions.count() > 1:
        submission2 = pending_submissions[1]
        print(f"\nSubmission ID: {submission2.id}")
        print(f"Title: {submission2.title}")
        print(f"Current tracking number: {submission2.tracking_number}")
        
        manual_number = "CUSTOM-2026-TEST-001"
        print(f"\nAttempting to assign manual tracking number: {manual_number}")
        
        try:
            TrackingService.assign_tracking_number(
                submission=submission2,
                mode='manual',
                manual_number=manual_number,
                actor=user
            )
            submission2.refresh_from_db()
            print(f"✓ Manual tracking number assigned: {submission2.tracking_number}")
            print(f"✓ Status changed to: {submission2.status}")
            print(f"✓ Tracking locked: {submission2.tracking_locked}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test duplicate manual number (should fail)
    print("\n" + "=" * 60)
    print("TEST 3: Duplicate Manual Number (Should Fail)")
    print("=" * 60)
    
    if pending_submissions.count() > 2:
        submission3 = pending_submissions[2]
        print(f"\nSubmission ID: {submission3.id}")
        print(f"Title: {submission3.title}")
        print(f"\nAttempting to assign duplicate tracking number: {manual_number}")
        
        try:
            TrackingService.assign_tracking_number(
                submission=submission3,
                mode='manual',
                manual_number=manual_number,
                actor=user
            )
            print(f"❌ UNEXPECTED: Duplicate was allowed!")
        except ValueError as e:
            print(f"✓ Correctly rejected duplicate: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    # Show all tracking numbers
    print("\n" + "=" * 60)
    print("ALL ASSIGNED TRACKING NUMBERS")
    print("=" * 60)
    
    assigned = Submission.objects.filter(
        tracking_number__isnull=False
    ).order_by('id')
    
    for sub in assigned:
        print(f"\nID: {sub.id}")
        print(f"  Title: {sub.title}")
        print(f"  Tracking: {sub.tracking_number}")
        print(f"  Status: {sub.status}")
        print(f"  Locked: {sub.tracking_locked}")

if __name__ == '__main__':
    test_tracking_modes()
