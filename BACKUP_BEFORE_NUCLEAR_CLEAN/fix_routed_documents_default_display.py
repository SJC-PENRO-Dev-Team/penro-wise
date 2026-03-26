#!/usr/bin/env python3
"""
Fix for Routed Documents Default Display Issue

PROBLEM:
The default routed documents display shows all accepted WorkItemAttachment files,
which includes workstate assets and other non-document-tracking files.

SOLUTION:
The routed documents tab should only show document tracking specific files by default.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment
from document_tracking.models import Submission
from structure.models import DocumentFolder

def analyze_current_default_display():
    """Analyze what the current default display is showing"""
    print("🔍 Analyzing Current Default Display")
    print("=" * 50)
    
    # Current default query (from all_files_view)
    current_files = WorkItemAttachment.objects.filter(
        acceptance_status="accepted"
    ).select_related(
        "uploaded_by",
        "work_item",
        "work_item__workcycle",
        "folder",
    ).order_by("-uploaded_at")
    
    print(f"📊 Current default display shows: {current_files.count()} files")
    
    # Analyze what types of files are included
    workstate_files = current_files.exclude(folder__folder_type='attachment').count()
    document_tracking_files = current_files.filter(folder__folder_type='attachment').count()
    other_files = current_files.filter(folder__isnull=True).count()
    
    print(f"   - Workstate assets: {workstate_files}")
    print(f"   - Document tracking files: {document_tracking_files}")
    print(f"   - Other files (no folder): {other_files}")
    
    # What should routed documents show?
    print(f"\n🎯 What Routed Documents SHOULD show:")
    
    # Get all document tracking submissions
    submissions = Submission.objects.all()
    print(f"   - Total submissions: {submissions.count()}")
    
    # Get folders related to submissions
    submission_folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            submission_folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            submission_folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            submission_folder_ids.append(submission.file_manager_folder_id)
    
    # Also get folders that reference submissions
    related_folders = DocumentFolder.objects.filter(
        models.Q(primary_submissions__in=submissions) |
        models.Q(archived_submissions__in=submissions) |
        models.Q(tracked_submissions__in=submissions)
    ).distinct()
    
    submission_folder_ids.extend([f.id for f in related_folders])
    submission_folder_ids = list(set(submission_folder_ids))  # Remove duplicates
    
    # Get attachments from submission folders
    routed_files = WorkItemAttachment.objects.filter(
        folder_id__in=submission_folder_ids,
        folder__folder_type='attachment'
    ).count()
    
    print(f"   - Document tracking folders: {len(submission_folder_ids)}")
    print(f"   - Routed document files: {routed_files}")
    
    print(f"\n❌ PROBLEM IDENTIFIED:")
    print(f"   Current default shows {current_files.count()} files (mixed content)")
    print(f"   Should show {routed_files} routed document files only")
    
    return {
        'current_total': current_files.count(),
        'workstate_files': workstate_files,
        'document_tracking_files': document_tracking_files,
        'should_show': routed_files,
        'submission_folders': len(submission_folder_ids)
    }

def propose_solution():
    """Propose the solution for fixing the default display"""
    print(f"\n💡 PROPOSED SOLUTION:")
    print("=" * 50)
    
    print("1. Update all_files_view.py:")
    print("   - Add routed_documents context variable")
    print("   - Query only document tracking related files")
    print("   - Separate from workstate assets")
    
    print("\n2. Update template:")
    print("   - Use routed_documents for Routed Documents tab")
    print("   - Keep files for backward compatibility")
    print("   - Show proper counts")
    
    print("\n3. Benefits:")
    print("   - Routed Documents shows only relevant files")
    print("   - Workstate Assets shows only workstate files")
    print("   - Clear separation of concerns")
    print("   - Better user experience")

if __name__ == "__main__":
    try:
        from django.db import models
        analysis = analyze_current_default_display()
        propose_solution()
        
        print(f"\n📋 SUMMARY:")
        print(f"   Current display: {analysis['current_total']} mixed files")
        print(f"   Should display: {analysis['should_show']} routed files")
        print(f"   Fix needed: ✅ YES")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)