"""
Management command to initialize the document folder structure.
Creates the ROOT folder if it doesn't exist.
"""
from django.core.management.base import BaseCommand
from structure.models import DocumentFolder


class Command(BaseCommand):
    help = 'Initialize the document folder structure (creates ROOT folder)'

    def handle(self, *args, **options):
        # Check if ROOT folder exists
        root_exists = DocumentFolder.objects.filter(
            folder_type=DocumentFolder.FolderType.ROOT,
            parent__isnull=True
        ).exists()

        if root_exists:
            self.stdout.write(
                self.style.SUCCESS('ROOT folder already exists.')
            )
            return

        # Create ROOT folder
        root = DocumentFolder.objects.create(
            name="ROOT",
            folder_type=DocumentFolder.FolderType.ROOT,
            parent=None,
            is_system_generated=True,
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created ROOT folder (ID: {root.id})')
        )
