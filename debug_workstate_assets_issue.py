#!/usr/bin/env python3
"""
Debug script to check why workstate assets endpoint doesn't load files
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, WorkCycle
from document_tracking.models import Submission
from django.db.models import Q

def debug_workstate_assets():
    print("=== DEBUGGING WORKSTATE ASSETS ISSUE ===\n")
    
    # 1. Check total WorkItemAttachment count
    total_attachments = WorkItemAttachment.objects.count()
    print(f"1. Total WorkItemAttachment objects: {total_attachments}")
    
    # 2. Check accepted attachments
    accepted_attachments = WorkItemAttachment.objects.filter(acceptance_status="accepted").count()
    print(f"2. Accepted WorkItemAttachment objects: {accepted_attachments}")
    
    # 3. Check document tracking folder exclusions
    submissions = Submission.objects.all()
    submission_folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            submission_folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            submission_folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            submission_folder_ids.append(submission.file_manager_folder_id)
    
    from structure.models import DocumentFolder
    related_folders = DocumentFolder.objects.filter(
        Q(primary_submissions__in=submissions) |
        Q(archived_submissions__in=submissions) |
        Q(tracked_submissions__in=submissions)
    ).distinct()
    
    submission_folder_ids.extend([f.id for f in related_folders])
    submission_folder_ids = list(set(submission_folder_ids))
    
    print(f"3. Document tracking folder IDs to exclude: {len(submission_folder_ids)} folders")
    print(f"   Folder IDs: {submission_folder_ids[:10]}{'...' if len(submission_folder_ids) > 10 else ''}")
    
    # 4. Check workstate queryset (what should be returned)
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
    print(f"4. Workstate assets after exclusions: {workstate_count}")
    
    # 5. Show some sample workstate assets
    if workstate_count > 0:
        print(f"\n5. Sample workstate assets (first 5):")
        for i, attachment in enumerate(workstate_qs[:5]):
            print(f"   {i+1}. ID: {attachment.id}")
            print(f"      File: {attachment.file.name if attachment.file else 'N/A'}")
            print(f"      Link: {attachment.link_url if attachment.is_link() else 'N/A'}")
            print(f"      Folder ID: {attachment.folder_id}")
            print(f"      Work Item: {attachment.work_item}")
            print(f"      Workcycle: {attachment.work_item.workcycle if attachment.work_item else 'N/A'}")
            print(f"      Uploaded: {attachment.uploaded_at}")
            print()
    else:
        print("\n5. No workstate assets found!")
        
        # Debug why no assets found
        print("\n   DEBUGGING NO ASSETS:")
        
        # Check if there are accepted attachments with folders
        accepted_with_folders = WorkItemAttachment.objects.filter(
            acceptance_status="accepted",
            folder_id__isnull=False
        )
        print(f"   - Accepted attachments with folders: {accepted_with_folders.count()}")
        
        # Check if all accepted attachments are in excluded folders
        accepted_in_excluded = WorkItemAttachment.objects.filter(
            acceptance_status="accepted",
            folder_id__in=submission_folder_ids
        ).count()
        print(f"   - Accepted attachments in excluded folders: {accepted_in_excluded}")
        
        # Check accepted attachments without folders
        accepted_no_folders = WorkItemAttachment.objects.filter(
            acceptance_status="accepted",
            folder_id__isnull=True
        ).count()
        print(f"   - Accepted attachments without folders: {accepted_no_folders}")
    
    # 6. Check WorkCycles for filter options
    workcycles = WorkCycle.objects.filter(is_active=True).count()
    print(f"\n6. Active WorkCycles for filters: {workcycles}")
    
    # 7. Check if there are any attachments at all in file manager
    print(f"\n7. File manager check:")
    all_attachments_with_work_items = WorkItemAttachment.objects.filter(
        work_item__isnull=False
    ).count()
    print(f"   - Attachments with work items: {all_attachments_with_work_items}")
    
    all_attachments_with_workcycles = WorkItemAttachment.objects.filter(
        work_item__workcycle__isnull=False
    ).count()
    print(f"   - Attachments with workcycles: {all_attachments_with_workcycles}")

if __name__ == "__main__":
    debug_workstate_assets()