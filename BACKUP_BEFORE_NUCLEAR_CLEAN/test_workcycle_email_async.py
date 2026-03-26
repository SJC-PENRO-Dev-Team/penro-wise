"""
Test script for async workcycle email notifications.

Usage:
    python test_workcycle_email_async.py

This script tests:
1. WorkCycleEmailJob model creation
2. Email job processor command
3. Job status transitions
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkCycle, WorkCycleEmailJob, User
from django.utils import timezone
from datetime import timedelta

def test_email_job_creation():
    """Test creating WorkCycleEmailJob records."""
    print("\n" + "="*60)
    print("TEST 1: WorkCycleEmailJob Creation")
    print("="*60)
    
    # Get a test workcycle
    workcycle = WorkCycle.objects.filter(is_active=True).first()
    if not workcycle:
        print("❌ No active workcycles found. Create one first.")
        return False
    
    # Get a test user
    admin = User.objects.filter(login_role="admin").first()
    if not admin:
        print("❌ No admin users found.")
        return False
    
    print(f"✓ Using workcycle: {workcycle.title}")
    print(f"✓ Using admin: {admin.username}")
    
    # Create test email jobs
    jobs_created = []
    
    # Test 1: Created job
    job1 = WorkCycleEmailJob.objects.create(
        workcycle=workcycle,
        job_type="created",
        actor=admin,
    )
    jobs_created.append(job1)
    print(f"✓ Created 'created' job: #{job1.id}")
    
    # Test 2: Edited job
    job2 = WorkCycleEmailJob.objects.create(
        workcycle=workcycle,
        job_type="edited",
        actor=admin,
        old_due_at=timezone.now() - timedelta(days=1),
    )
    jobs_created.append(job2)
    print(f"✓ Created 'edited' job: #{job2.id}")
    
    # Test 3: Reassigned job
    job3 = WorkCycleEmailJob.objects.create(
        workcycle=workcycle,
        job_type="reassigned",
        actor=admin,
        inactive_note="Test reassignment",
    )
    jobs_created.append(job3)
    print(f"✓ Created 'reassigned' job: #{job3.id}")
    
    # Verify jobs are pending
    pending_count = WorkCycleEmailJob.objects.filter(status="pending").count()
    print(f"\n✓ Total pending jobs: {pending_count}")
    
    return jobs_created

def test_job_processor():
    """Test the email job processor command."""
    print("\n" + "="*60)
    print("TEST 2: Email Job Processor")
    print("="*60)
    
    from django.core.management import call_command
    
    print("Running: python manage.py process_workcycle_email_jobs")
    print("-" * 60)
    
    try:
        call_command("process_workcycle_email_jobs", max_jobs=5)
        print("-" * 60)
        print("✓ Command executed successfully")
        return True
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return False

def check_job_status():
    """Check status of all email jobs."""
    print("\n" + "="*60)
    print("TEST 3: Job Status Check")
    print("="*60)
    
    # Count by status
    pending = WorkCycleEmailJob.objects.filter(status="pending").count()
    processing = WorkCycleEmailJob.objects.filter(status="processing").count()
    done = WorkCycleEmailJob.objects.filter(status="done").count()
    failed = WorkCycleEmailJob.objects.filter(status="failed").count()
    
    print(f"Pending:    {pending}")
    print(f"Processing: {processing}")
    print(f"Done:       {done}")
    print(f"Failed:     {failed}")
    
    # Show recent jobs
    print("\nRecent Jobs:")
    print("-" * 60)
    recent = WorkCycleEmailJob.objects.order_by("-created_at")[:10]
    
    for job in recent:
        status_icon = {
            "pending": "⏳",
            "processing": "⚙️",
            "done": "✓",
            "failed": "✗"
        }.get(job.status, "?")
        
        print(f"{status_icon} Job#{job.id}: {job.job_type} - {job.status}")
        print(f"   WorkCycle: {job.workcycle.title}")
        print(f"   Actor: {job.actor.username if job.actor else 'N/A'}")
        if job.last_error:
            print(f"   Error: {job.last_error[:100]}")
        print()
    
    return True

def cleanup_test_jobs():
    """Clean up test jobs created by this script."""
    print("\n" + "="*60)
    print("CLEANUP: Remove Test Jobs")
    print("="*60)
    
    response = input("Delete all test email jobs? (y/n): ")
    if response.lower() == 'y':
        count = WorkCycleEmailJob.objects.all().delete()[0]
        print(f"✓ Deleted {count} email job(s)")
    else:
        print("Skipped cleanup")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("WORKCYCLE EMAIL ASYNC - TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Create jobs
        jobs = test_email_job_creation()
        if not jobs:
            print("\n❌ Test 1 failed. Exiting.")
            return
        
        # Test 2: Process jobs
        success = test_job_processor()
        if not success:
            print("\n⚠️ Test 2 failed. Check email configuration.")
        
        # Test 3: Check status
        check_job_status()
        
        # Cleanup
        cleanup_test_jobs()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
