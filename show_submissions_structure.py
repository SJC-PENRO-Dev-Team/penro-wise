#!/usr/bin/env python
"""Show the complete folder structure under Submissions"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder
from accounts.models import WorkItemAttachment

def show_tree(folder, indent=0):
    """Recursively show folder tree"""
    prefix = "  " * indent
    icon = "📁" if folder.folder_type != 'attachment' else "📂"
    
    # Count files in this folder
    file_count = WorkItemAttachment.objects.filter(folder=folder, acceptance_status='accepted').count()
    file_info = f" ({file_count} files)" if file_count > 0 else ""
    
    print(f"{prefix}{icon} {folder.name} ({folder.folder_type}){file_info} - ID: {folder.id}")
    
    # Show files if any
    if file_count > 0:
        files = WorkItemAttachment.objects.filter(folder=folder, acceptance_status='accepted')
        for file in files[:5]:  # Show first 5 files
            print(f"{prefix}  📄 {file.get_filename()}")
        if file_count > 5:
            print(f"{prefix}  ... and {file_count - 5} more files")
    
    # Recursively show children
    for child in folder.children.all().order_by('name'):
        show_tree(child, indent + 1)

print("=" * 80)
print("SUBMISSIONS FOLDER STRUCTURE")
print("=" * 80)

try:
    submissions = DocumentFolder.objects.get(id=85, name="Submissions", folder_type='category')
    
    print(f"\nLocation: ROOT > 2026 > Submissions")
    print(f"Folder ID: {submissions.id}")
    print(f"Type: {submissions.folder_type}")
    print(f"Direct children: {submissions.children.count()}")
    
    print("\n" + "=" * 80)
    print("COMPLETE TREE")
    print("=" * 80)
    print()
    
    show_tree(submissions)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Count all descendants
    def count_descendants(folder):
        count = 0
        for child in folder.children.all():
            count += 1
            count += count_descendants(child)
        return count
    
    total_folders = count_descendants(submissions)
    total_files = WorkItemAttachment.objects.filter(
        folder__in=DocumentFolder.objects.filter(
            id__in=[submissions.id] + [f.id for f in DocumentFolder.objects.filter(parent=submissions)]
        ),
        acceptance_status='accepted'
    ).count()
    
    print(f"\nTotal subfolders: {total_folders}")
    print(f"Total files: {total_files}")
    
except DocumentFolder.DoesNotExist:
    print("\n❌ Submissions folder not found!")

print("\n" + "=" * 80)
