"""
Management command to create default document types.
"""
from django.core.management.base import BaseCommand
from document_tracking.models import DocumentType


class Command(BaseCommand):
    help = 'Create default document types for tracking system'

    def handle(self, *args, **options):
        default_types = [
            {
                'name': 'General Document',
                'prefix': 'GEN',
                'description': 'General purpose documents',
                'order': 1,
                'serial_mode': 'auto',
                'reset_annually': True,
            },
            {
                'name': 'Memorandum',
                'prefix': 'MEM',
                'description': 'Internal memorandums and communications',
                'order': 2,
                'serial_mode': 'auto',
                'reset_annually': True,
            },
            {
                'name': 'Letter',
                'prefix': 'LTR',
                'description': 'Official letters and correspondence',
                'order': 3,
                'serial_mode': 'auto',
                'reset_annually': True,
            },
            {
                'name': 'Report',
                'prefix': 'RPT',
                'description': 'Reports and analytical documents',
                'order': 4,
                'serial_mode': 'auto',
                'reset_annually': True,
            },
            {
                'name': 'Permit Application',
                'prefix': 'PRM',
                'description': 'Permit applications and requests',
                'order': 5,
                'serial_mode': 'auto',
                'reset_annually': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for type_data in default_types:
            doc_type, created = DocumentType.objects.get_or_create(
                prefix=type_data['prefix'],
                defaults=type_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {doc_type.name} ({doc_type.prefix})')
                )
            else:
                # Update existing if needed
                updated = False
                for key, value in type_data.items():
                    if key != 'prefix' and getattr(doc_type, key) != value:
                        setattr(doc_type, key, value)
                        updated = True
                
                if updated:
                    doc_type.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated: {doc_type.name} ({doc_type.prefix})')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'  Exists: {doc_type.name} ({doc_type.prefix})')
                    )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {DocumentType.objects.count()}'))
