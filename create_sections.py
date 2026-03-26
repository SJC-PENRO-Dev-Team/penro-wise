"""
Create required Section records for Document Tracking System.

This script creates the three required sections:
- Licensing
- Enforcement  
- Admin

Usage:
    python create_sections.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Section


def create_sections():
    """Create the required sections if they don't exist."""
    print("\n" + "="*60)
    print("CREATING DOCUMENT TRACKING SECTIONS")
    print("="*60)
    
    sections_data = [
        ('licensing', 'Licensing'),
        ('enforcement', 'Enforcement'),
        ('admin', 'Admin'),
    ]
    
    created_count = 0
    existing_count = 0
    
    for section_code, section_name in sections_data:
        section, created = Section.objects.get_or_create(
            name=section_code,
            defaults={'name': section_code}
        )
        
        if created:
            print(f"✅ Created: {section_name} ({section_code})")
            created_count += 1
        else:
            print(f"ℹ️  Already exists: {section_name} ({section_code})")
            existing_count += 1
    
    print("\n" + "="*60)
    print(f"Summary: {created_count} created, {existing_count} already existed")
    print("="*60)
    
    # Show all sections
    print("\nAll sections in database:")
    for section in Section.objects.all():
        officer_count = section.officers.count()
        print(f"  - {section.get_name_display()} ({section.name}) - {officer_count} officers")
    
    print("\n✅ Sections setup complete!")
    print("\nRouting map:")
    print("  - permit → Licensing")
    print("  - inspection → Enforcement")
    print("  - memo → Admin")
    print("  - others → Admin")


if __name__ == '__main__':
    create_sections()
