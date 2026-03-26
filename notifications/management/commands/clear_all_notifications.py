"""
Clear all notifications from the database
Run with: python manage.py clear_all_notifications
"""

from django.core.management.base import BaseCommand
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Clear all notifications from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of all notifications',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  This will DELETE ALL notifications!\n'
                    'Run with --confirm flag to proceed:\n'
                    '  python manage.py clear_all_notifications --confirm\n'
                )
            )
            return

        count = Notification.objects.count()
        
        self.stdout.write(f"\nDeleting {count} notifications...")
        
        Notification.objects.all().delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully deleted {count} notifications\n'
                'New notifications will be created with correct URLs.\n'
            )
        )
