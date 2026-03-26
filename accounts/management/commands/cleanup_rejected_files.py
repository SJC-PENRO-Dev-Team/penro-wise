"""
Management command to clean up expired rejected files.
Run this periodically (e.g., via cron or scheduled task).

Usage:
    python manage.py cleanup_rejected_files
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import WorkItemAttachment


class Command(BaseCommand):
    help = "Delete rejected files that have expired (24 hours after rejection)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        # Find expired rejected files
        expired_files = WorkItemAttachment.objects.filter(
            acceptance_status="rejected",
            rejection_expires_at__lte=now,
        )

        count = expired_files.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("No expired rejected files to clean up.")
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: Would delete {count} expired files:")
            )
            for attachment in expired_files:
                file_name = getattr(attachment.file, 'name', str(attachment.file)) if attachment.file else 'unknown'
                self.stdout.write(f"  - {file_name} (rejected at {attachment.rejected_at})")
            return

        # Delete files
        deleted_count = 0
        for attachment in expired_files:
            try:
                file_name = getattr(attachment.file, 'name', str(attachment.file)) if attachment.file else 'unknown'
                
                # Delete the actual file from storage (works with both local and Cloudinary)
                if attachment.file:
                    try:
                        attachment.file.delete(save=False)
                        self.stdout.write(f"  Deleted file: {file_name}")
                    except Exception as file_error:
                        self.stdout.write(
                            self.style.WARNING(f"  Could not delete file {file_name}: {file_error}")
                        )

                # Delete the database record
                attachment.delete()
                deleted_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error deleting attachment: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} expired rejected files.")
        )
