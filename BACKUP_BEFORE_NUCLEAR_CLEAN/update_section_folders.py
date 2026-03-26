"""
Update existing section folders to be system-generated (blue color).

This script updates the Licensing, Enforcement, and Admin folders
under Submissions to be system-generated so they display in blue.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from structure.models import DocumentFolder

def update_section_folders():
    """Update section folders to be system-generated."""
    
    # Find all Submissions folders
    submissions_folders = DocumentFolder.objects.filter(
        name="Submissions",
        folder_type=DocumentFolder.FolderType.CATEGORY
    )
    
    if not submissions_folders.exists():
        print("✗ No Submissions folders found")
        return
    
    print(f"Found {submissions_folders.count()} Submissions folder(s):\n")
    
    # Section names to update
    section_names = ["Licensing", "Enforcement", "Admin"]
    
    total_updated = 0
    for submissions_folder in submissions_folders:
        print(f"Processing: {submissions_folder.get_path_string()}")
        
        updated_count = 0
        for section_name in section_names:
            try:
                section_folder = DocumentFolder.objects.get(
                    name=section_name,
                    parent=submissions_folder,
                    folder_type=DocumentFolder.FolderType.ATTACHMENT
                )
                
                if not section_folder.is_system_generated:
                    section_folder.is_system_generated = True
                    section_folder.save()
                    print(f"  ✓ Updated {section_name} folder to system-generated (blue)")
                    updated_count += 1
                else:
                    print(f"    {section_name} folder is already system-generated")
                    
            except DocumentFolder.DoesNotExist:
                print(f"    {section_name} folder not found (will be created on next approval)")
            except DocumentFolder.MultipleObjectsReturned:
                print(f"  ✗ Multiple {section_name} folders found - manual cleanup needed")
        
        total_updated += updated_count
        print()
    
    print(f"✓ Updated {total_updated} section folder(s) total")
    print("\nSection folders will now display in blue in File Manager!")

if __name__ == "__main__":
    print("Updating section folders to be system-generated...\n")
    update_section_folders()
