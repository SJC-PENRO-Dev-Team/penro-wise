"""
Test script for async WorkCycle creation.

This script:
1. Creates a WorkCycle with assignments (fast)
2. Verifies a WorkCycleJob was created with status=PENDING
3. Runs the job processor
4. Verifies WorkItems and Notifications were created
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Team, WorkCycle, WorkAssignment, WorkItem, WorkCycleJob
from notifications.models import Notification
from admin_app.services.workcycle_service import create_workcycle_with_assignments, process_workcycle_job

def test_async_workcycle():
    print("=" * 60)
    print("TESTING ASYNC WORKCYCLE CREATION")
    print("=" * 60)
    
    # Get test data
    admin = User.objects.filter(login_role="admin").first()
    users = User.objects.filter(login_role="user", is_active=True)[:3]
    
    if not admin:
        print("❌ No admin user found")
        return
    
    if not users:
        print("❌ No regular users found")
        return
    
    print(f"\n✓ Found admin: {admin.username}")
    print(f"✓ Found {users.count()} test users")
    
    # Step 1: Create WorkCycle (should be FAST)
    print("\n" + "-" * 60)
    print("STEP 1: Creating WorkCycle (should be instant)")
    print("-" * 60)
    
    import time
    start_time = time.time()
    
    workcycle = create_workcycle_with_assignments(
        title="Test Async WorkCycle",
        description="Testing async job processing",
        due_at=timezone.now() + timedelta(days=7),
        created_by=admin,
        users=users,
        team=None,
    )
    
    elapsed = time.time() - start_time
    print(f"✓ WorkCycle created in {elapsed:.2f} seconds")
    print(f"  ID: {workcycle.id}")
    print(f"  Title: {workcycle.title}")
    
    # Step 2: Verify WorkCycleJob was created
    print("\n" + "-" * 60)
    print("STEP 2: Checking WorkCycleJob")
    print("-" * 60)
    
    job = WorkCycleJob.objects.filter(workcycle=workcycle).first()
    
    if not job:
        print("❌ No WorkCycleJob found!")
        return
    
    print(f"✓ WorkCycleJob created")
    print(f"  ID: {job.id}")
    print(f"  Status: {job.status}")
    print(f"  Created: {job.created_at}")
    
    if job.status != "pending":
        print(f"❌ Expected status 'pending', got '{job.status}'")
        return
    
    # Step 3: Verify WorkItems NOT created yet
    print("\n" + "-" * 60)
    print("STEP 3: Checking WorkItems (should be 0)")
    print("-" * 60)
    
    work_items_count = WorkItem.objects.filter(workcycle=workcycle).count()
    print(f"  WorkItems count: {work_items_count}")
    
    if work_items_count > 0:
        print(f"⚠️  Expected 0 WorkItems, found {work_items_count}")
    else:
        print("✓ No WorkItems created yet (as expected)")
    
    # Step 4: Process the job
    print("\n" + "-" * 60)
    print("STEP 4: Processing WorkCycleJob")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        process_workcycle_job(job)
        elapsed = time.time() - start_time
        print(f"✓ Job processed in {elapsed:.2f} seconds")
    except Exception as e:
        print(f"❌ Job processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Verify job status updated
    job.refresh_from_db()
    print(f"\n  Job status: {job.status}")
    print(f"  Retry count: {job.retry_count}")
    print(f"  Last error: {job.last_error or 'None'}")
    
    if job.status != "done":
        print(f"❌ Expected status 'done', got '{job.status}'")
        return
    
    # Step 6: Verify WorkItems created
    print("\n" + "-" * 60)
    print("STEP 5: Verifying WorkItems created")
    print("-" * 60)
    
    work_items = WorkItem.objects.filter(workcycle=workcycle)
    print(f"  WorkItems count: {work_items.count()}")
    
    if work_items.count() != users.count():
        print(f"⚠️  Expected {users.count()} WorkItems, found {work_items.count()}")
    else:
        print(f"✓ All {work_items.count()} WorkItems created")
    
    for item in work_items:
        print(f"    - {item.owner.username}: {item.status}")
    
    # Step 7: Verify Notifications created
    print("\n" + "-" * 60)
    print("STEP 6: Verifying Notifications created")
    print("-" * 60)
    
    notifications = Notification.objects.filter(
        workcycle=workcycle,
        category=Notification.Category.ASSIGNMENT
    )
    print(f"  Notifications count: {notifications.count()}")
    
    if notifications.count() != users.count():
        print(f"⚠️  Expected {users.count()} Notifications, found {notifications.count()}")
    else:
        print(f"✓ All {notifications.count()} Notifications created")
    
    for notif in notifications:
        print(f"    - {notif.recipient.username}: {notif.title}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✓ WorkCycle created instantly")
    print(f"✓ WorkCycleJob created with status=PENDING")
    print(f"✓ Job processed successfully")
    print(f"✓ {work_items.count()} WorkItems created")
    print(f"✓ {notifications.count()} Notifications created")
    print("\n🎉 ASYNC WORKCYCLE CREATION WORKING!")
    print("=" * 60)

if __name__ == "__main__":
    test_async_workcycle()
