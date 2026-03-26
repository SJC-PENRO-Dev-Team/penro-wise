"""
Management command to create default sections/departments.

Usage:
    python manage.py create_default_sections
"""
from django.core.management.base import BaseCommand
from document_tracking.models import Section


class Command(BaseCommand):
    help = 'Create default sections/departments for document tracking'

    def handle(self, *args, **options):
        """Create default sections."""
        sections_data = [
            {
                'name': 'licensing',
                'display_name': 'Licensing',
                'description': 'Handles licensing applications and permits',
                'order': 1,
            },
            {
                'name': 'enforcement',
                'display_name': 'Enforcement',
                'description': 'Handles enforcement actions and violations',
                'order': 2,
            },
            {
                'name': 'admin',
                'display_name': 'Admin',
                'description': 'Administrative and general documents',
                'order': 3,
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for data in sections_data:
            section, created = Section.objects.get_or_create(
                name=data['name'],
                defaults={
                    'display_name': data['display_name'],
                    'description': data['description'],
                    'order': data['order'],
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created section: {section.display_name}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Section already exists: {section.display_name}')
                )
                existing_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  - Created: {created_count}')
        self.stdout.write(f'  - Already existed: {existing_count}')
        self.stdout.write(f'  - Total: {created_count + existing_count}')
