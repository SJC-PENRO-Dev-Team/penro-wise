#!/usr/bin/env python3
"""
Analyze routed documents data structure for proper filtering
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType, Section
from accounts.models import WorkItemAttachment

def analyze_routed_documents():
    """Analyze the routed documents data structure"""
    
    print("🔍 ROUTED DOCUMENTS DATA ANALYSIS")
    print("=" * 50)
    
    # Check submissions
    submissions = Submission.objects.all()
    print(f"📊 Total Submissions: {submissions.count()}")
    
    if submissions.exists():
        print("\n📋 Sample Submissions:")
        for sub in submissions[:5]:
            print(f"  - ID: {sub.id}")
            print(f"    Title: {sub.title}")
            print(f"    Status: {sub.get_status_display()}")
            print(f"    Document Type: {sub.document_type}")
            print(f"    Doc Type (FK): {sub.doc_type}")
            print(f"    Tracking: {sub.tracking_number}")
            print(f"    Section: {sub.assigned_section}")
            print(f"    Submitted by: {sub.submitted_by}")
            print()
    
    # Check document types
    doc_types = DocumentType.objects.all()
    print(f"📄 Document Types: {doc_types.count()}")
    for dt in doc_types:
        submission_count = Submission.objects.filter(doc_type=dt).count()
        print(f"  - {dt.name} ({dt.prefix}): {submission_count} submissions")
    
    # Check sections
    sections = Section.objects.all()
    print(f"\n🏢 Sections: {sections.count()}")
    for section in sections:
        submission_count = Submission.objects.filter(assigned_section=section).count()
        print(f"  - {section.name}: {submission_count} submissions")
    
    # Check status distribution
    print(f"\n📈 Status Distribution:")
    for status_code, status_display in Submission.STATUS_CHOICES:
        count = Submission.objects.filter(status=status_code).count()
        print(f"  - {status_display}: {count} submissions")
    
    # Check routed document attachments
    routed_attachments = WorkItemAttachment.objects.filter(
        folder__folder_type='attachment'
    ).select_related('folder')
    
    print(f"\n📎 Routed Document Attachments: {routed_attachments.count()}")
    
    # Find submissions with attachments
    submissions_with_files = []
    for att in routed_attachments:
        # Find submission through folder relationships
        folder = att.folder
        submission = None
        
        # Check if folder has submission relationships
        if hasattr(folder, 'primary_submissions') and folder.primary_submissions.exists():
            submission = folder.primary_submissions.first()
        elif hasattr(folder, 'archived_submissions') and folder.archived_submissions.exists():
            submission = folder.archived_submissions.first()
        elif hasattr(folder, 'tracked_submissions') and folder.tracked_submissions.exists():
            submission = folder.tracked_submissions.first()
        
        if submission and submission not in submissions_with_files:
            submissions_with_files.append(submission)
            print(f"  - Submission: {submission.title}")
            print(f"    Status: {submission.get_status_display()}")
            print(f"    Files: {routed_attachments.filter(folder__primary_submissions=submission).count() + routed_attachments.filter(folder__archived_submissions=submission).count() + routed_attachments.filter(folder__tracked_submissions=submission).count()}")
    
    print(f"\n📊 Summary:")
    print(f"  - Total submissions: {submissions.count()}")
    print(f"  - Submissions with files: {len(submissions_with_files)}")
    print(f"  - Total routed attachments: {routed_attachments.count()}")
    
    return {
        'submissions': submissions,
        'document_types': doc_types,
        'sections': sections,
        'routed_attachments': routed_attachments,
        'submissions_with_files': submissions_with_files
    }

def suggest_filters(data):
    """Suggest appropriate filters based on data analysis"""
    
    print("\n🎯 SUGGESTED FILTERS FOR ROUTED DOCUMENTS")
    print("=" * 50)
    
    print("1. 📄 Document Type Filter")
    print("   - Based on: submission.doc_type (DocumentType FK)")
    print("   - Options:")
    for dt in data['document_types']:
        count = Submission.objects.filter(doc_type=dt).count()
        print(f"     • {dt.name} ({count} submissions)")
    
    print("\n2. 📈 Status Filter")
    print("   - Based on: submission.status")
    print("   - Options:")
    for status_code, status_display in Submission.STATUS_CHOICES:
        count = Submission.objects.filter(status=status_code).count()
        if count > 0:
            print(f"     • {status_display} ({count} submissions)")
    
    print("\n3. 🏢 Section Filter")
    print("   - Based on: submission.assigned_section")
    print("   - Options:")
    for section in data['sections']:
        count = Submission.objects.filter(assigned_section=section).count()
        print(f"     • {section.name} ({count} submissions)")
    
    print("\n4. 📅 Date Range Filter")
    print("   - Based on: submission.created_at")
    print("   - Options: Date picker or predefined ranges")
    
    print("\n5. 👤 Submitted By Filter")
    print("   - Based on: submission.submitted_by")
    print("   - Options: User dropdown")

if __name__ == "__main__":
    print("🚀 Starting Routed Documents Analysis\n")
    
    try:
        data = analyze_routed_documents()
        suggest_filters(data)
        
        print("\n🎉 Analysis completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Analysis failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)