"""
Management command to fix action URLs for existing message notifications.
Updates all message notifications to point to the correct discussions list page.
"""

from django.core.management.base import BaseCommand
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Fix action URLs for existing message notifications'

    def handle(self, *args, **options):
        # Get all message notifications
        message_notifications = Notification.objects.filter(category='message')
        
        updated_count = 0
        
        for notif in message_notifications:
            # Determine correct URL based on recipient role
            if notif.recipient.login_role == 'admin':
                correct_url = '/admin/discussions/'
            else:
                correct_url = '/user/discussions/'
            
            # Update if different
            if notif.action_url != correct_url:
                notif.action_url = correct_url
                notif.save(update_fields=['action_url'])
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} message notification URLs'
            )
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Total message notifications: {message_notifications.count()}'
            )
        )
