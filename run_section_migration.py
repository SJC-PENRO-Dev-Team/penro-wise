"""
Script to run the section migration.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
django.setup()

from django.core.management import call_command

print("Running section migration...")
print("="*60)

try:
    # Run the migration
    call_command('migrate', 'document_tracking', verbosity=2)
    print("\n" + "="*60)
    print("✓ Migration completed successfully!")
    print("="*60)
    
    # Show current sections
    from document_tracking.models import Section
    sections = Section.objects.all()
    
    print(f"\nCurrent sections ({sections.count()}):")
    for section in sections:
        print(f"  - {section.name}: {section.display_name}")
        print(f"    Active: {section.is_active}, Order: {section.order}")
        if section.description:
            print(f"    Description: {section.description}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
