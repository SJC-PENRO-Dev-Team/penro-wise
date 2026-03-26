from django.core.management.base import BaseCommand
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Clear all message notifications to regenerate with updated URLs'

    def handle(self, *args, **options):
        deleted_count, _ = Notification.objects.filter(category='message').delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {deleted_count} message notifications')
        )
