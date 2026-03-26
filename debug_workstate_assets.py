#!/usr/bin/env python3
"""
Debug script to investigate why workstate assets endpoint shows no files
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, WorkCycle
from document_tracking.models import Submission
from structure.models import DocumentFolder
from django.db.models import Q

def debug_workstate_assets():
    """Debug the workstate assets query to understand why no files are showing"""
    
    print("🔍 DEBUGGING WORKSTATE ASSETS ENDPOINT")
    print("=" * 50)
    
    # Step 1: Check total attachments
    total_attachments = WorkItemAttachment.objects.count()
    accepted_attachments = WorkItemAttachment.objects.filter(acceptance_status="accepted").count()
    print(f"📊 Total attachments in database: {total_attachments}")
    print(f"📊 Accepted attachments: {accepted_attachments}")
    
    # Step 2: Check document tracking exclusions
    print(f"\n📁 DOCUMENT TRACKING EXCLUSIONS")
    print("-" * 30)
    
    submissions = Submission.objects.all()
    submission_count = submissions.count()
    print(f"📄 Total submissions: {submission_count}")
    
    submission_folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            submission_folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            submission_folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            submission_folder_ids.append(submission.file_manager_folder_id)
    
    related_folders = DocumentFolder.objects.filter(
        Q(primary_submissions__in=submissions) |
        Q(archived_submissions__in=submissions) |
        Q(tracked_submissions__in=submissions)
    ).distinct()
    
    submission_folder_ids.extend([f.id for f in related_folders])
    submission_folder_ids = list(set(submission_folder_ids))
    
    print(f"📁 Document tracking folder IDs to exclude: {len(submission_folder_ids)}")
    print(f"📁 Folder IDs: {submission_folder_ids[:10]}{'...' if len(submission_folder_ids) > 10 else ''}")
    
    # Step 3: Check workstate query
    print(f"\n🔧 WORKSTATE QUERY ANALYSIS")
    print("-" * 30)
    
    # Base workstate query
    workstate_qs = (
        WorkItemAttachment.objects
        .filter(acceptance_status="accepted")
        .exclude(folder_id__in=submission_folder_ids)
        .select_related(
            "uploaded_by",
            "reviewed_by", 
            "work_item",
            "work_item__workcycle",
            "folder",
            "folder__workcycle",
        )
        .order_by("-uploaded_at")
    )
    
    workstate_count = workstate_qs.count()
    print(f"📊 Workstate assets (after exclusions): {workstate_count}")
    
    # Step 4: Analyze the attachments
    print(f"\n📋 ATTACHMENT ANALYSIS")
    print("-" * 30)
    
    # Check attachments by work_item relationship
    with_work_item = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__isnull=False
    ).count()
    
    without_work_item = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__isnull=True
    ).count()
    
    print(f"📊 Attachments with work_item: {with_work_item}")
    print(f"📊 Attachments without work_item: {without_work_item}")
    
    # Check by folder relationship
    with_folder = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        folder__isnull=False
    ).count()
    
    without_folder = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        folder__isnull=True
    ).count()
    
    print(f"📊 Attachments with folder: {with_folder}")
    print(f"📊 Attachments without folder: {without_folder}")
    
    # Step 5: Sample some attachments to understand their structure
    print(f"\n📝 SAMPLE ATTACHMENTS")
    print("-" * 30)
    
    sample_attachments = WorkItemAttachment.objects.filter(
        acceptance_status="accepted"
    ).select_related('work_item', 'folder')[:5]
    
    for i, attachment in enumerate(sample_attachments, 1):
        print(f"📎 Attachment {i}:")
        print(f"   ID: {attachment.id}")
        print(f"   File: {attachment.file.name if attachment.file else 'No file'}")
        print(f"   Work Item: {attachment.work_item.id if attachment.work_item else 'None'}")
        print(f"   Folder: {attachment.folder.id if attachment.folder else 'None'}")
        print(f"   Folder in exclusions: {attachment.folder.id in submission_folder_ids if attachment.folder else 'N/A'}")
        print(f"   Is Link: {attachment.is_link()}")
        print()
    
    # Step 6: Check WorkCycles
    print(f"\n🔄 WORKCYCLE ANALYSIS")
    print("-" * 30)
    
    total_workcycles = WorkCycle.objects.count()
    active_workcycles = WorkCycle.objects.filter(is_active=True).count()
    
    print(f"📊 Total WorkCycles: {total_workcycles}")
    print(f"📊 Active WorkCycles: {active_workcycles}")
    
    # Check attachments by workcycle
    attachments_with_workcycle = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__workcycle__isnull=False
    ).count()
    
    print(f"📊 Attachments with WorkCycle: {attachments_with_workcycle}")
    
    # Step 7: Test the exact workstate query logic
    print(f"\n🧪 TESTING WORKSTATE LOGIC")
    print("-" * 30)
    
    # Test without exclusions first
    all_accepted = WorkItemAttachment.objects.filter(acceptance_status="accepted").count()
    print(f"📊 All accepted attachments: {all_accepted}")
    
    # Test with exclusions
    after_exclusions = WorkItemAttachment.objects.filter(
        acceptance_status="accepted"
    ).exclude(folder_id__in=submission_folder_ids).count()
    print(f"📊 After document tracking exclusions: {after_exclusions}")
    
    # Check if the issue is with the folder exclusion logic
    if submission_folder_ids:
        excluded_attachments = WorkItemAttachment.objects.filter(
            acceptance_status="accepted",
            folder_id__in=submission_folder_ids
        ).count()
        print(f"📊 Attachments excluded (document tracking): {excluded_attachments}")
    
    # Step 8: Alternative query approach
    print(f"\n🔄 ALTERNATIVE APPROACH")
    print("-" * 30)
    
    # Try a simpler approach - get all accepted attachments that have work_items
    simple_workstate = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__isnull=False
    ).count()
    
    print(f"📊 Simple workstate query (has work_item): {simple_workstate}")
    
    # Check if any of these have files
    with_files = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__isnull=False,
        file__isnull=False
    ).exclude(file='').count()
    
    print(f"📊 Workstate attachments with actual files: {with_files}")
    
    # Check links
    with_links = WorkItemAttachment.objects.filter(
        acceptance_status="accepted",
        work_item__isnull=False,
        attachment_type='link'
    ).count()
    
    print(f"📊 Workstate attachments that are links: {with_links}")
    
    print(f"\n🎯 DIAGNOSIS COMPLETE")
    print("=" * 50)
    
    if workstate_count == 0:
        print("❌ ISSUE FOUND: No workstate assets after exclusions")
        if submission_folder_ids:
            print("💡 LIKELY CAUSE: Document tracking exclusions are too broad")
            print("💡 SOLUTION: Review folder exclusion logic")
        else:
            print("💡 LIKELY CAUSE: No work_item relationships or acceptance_status issues")
    else:
        print(f"✅ Query returns {workstate_count} workstate assets")
        print("💡 Issue might be in the template rendering or JavaScript")

if __name__ == "__main__":
    debug_workstate_assets()