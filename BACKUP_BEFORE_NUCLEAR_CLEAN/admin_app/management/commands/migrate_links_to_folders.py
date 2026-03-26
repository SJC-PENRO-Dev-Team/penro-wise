"""
Management command to migrate old links (with folder=None) to ROOT folder.
This is needed after changing links from global to folder-specific.

Usage:
    python manage.py migrate_links_to_folders
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import WorkItemAttachment
from structure.models import DocumentFolder


class Command(BaseCommand):
    help = 'Migrates old links (with folder=None) to the ROOT folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('Migrating old links to ROOT folder'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        # Get ROOT folder
        try:
            root_folder = DocumentFolder.objects.get(
                folder_type=DocumentFolder.FolderType.ROOT,
                parent__isnull=True
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Found ROOT folder: {root_folder.name} (ID: {root_folder.id})'))
        except DocumentFolder.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ ROOT folder not found!'))
            self.stdout.write(self.style.ERROR('  Please ensure the ROOT folder exists before running this command.'))
            return
        except DocumentFolder.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR('✗ Multiple ROOT folders found!'))
            self.stdout.write(self.style.ERROR('  Please fix the database before running this command.'))
            return
        
        # Find all links with folder=None
        old_links = WorkItemAttachment.objects.filter(
            link_url__isnull=False,
            folder__isnull=True
        )
        
        count = old_links.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No old links found. All links are already assigned to folders.'))
            return
        
        self.stdout.write(f'\nFound {count} old link(s) with folder=None:')
        self.stdout.write('-' * 70)
        
        # Show details
        for link in old_links[:10]:  # Show first 10
            self.stdout.write(f'  • ID: {link.id} | Title: {link.link_title or "Untitled"} | URL: {link.link_url[:50]}...')
        
        if count > 10:
            self.stdout.write(f'  ... and {count - 10} more')
        
        self.stdout.write('-' * 70)
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] Would migrate {count} link(s) to ROOT folder'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to perform the migration'))
            return
        
        # Perform migration
        self.stdout.write(f'\nMigrating {count} link(s) to ROOT folder...')
        
        try:
            with transaction.atomic():
                # Migrate one by one to avoid unique constraint issues
                updated = 0
                for link in old_links:
                    link.folder = root_folder
                    link.save()
                    updated += 1
                    self.stdout.write(f'  ✓ Migrated link {link.id}: {link.link_title or "Untitled"}')
                
                self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully migrated {updated} link(s) to ROOT folder'))
                self.stdout.write(self.style.SUCCESS(f'  All old links are now visible in: {root_folder.name}'))
                self.stdout.write(self.style.SUCCESS(f'  You can now move them to appropriate folders using the file manager'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Migration failed: {str(e)}'))
            raise
        
        self.stdout.write(self.style.WARNING('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('Migration complete!'))
        self.stdout.write(self.style.WARNING('=' * 70))
