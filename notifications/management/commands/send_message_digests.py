"""
Management command to send bulk email digests for unread discussion messages.

Usage:
    python manage.py send_message_digests

This command should be scheduled to run periodically (e.g., daily or every few hours)
via cron job or task scheduler.

Example cron entry (run daily at 8 AM):
    0 8 * * * cd /path/to/project && python manage.py send_message_digests
"""

from django.core.management.base import BaseCommand
from notifications.services.discussion_messages import send_all_pending_message_digests


class Command(BaseCommand):
    help = 'Send bulk email digests for unread discussion messages to all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send digest to a specific user ID only (for testing)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No emails will be sent'))
        
        if user_id:
            # Send to specific user
            from notifications.services.discussion_messages import send_message_digest_to_user, get_unread_messages_for_user
            from accounts.models import User
            
            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found or inactive'))
                return
            
            unread_data = get_unread_messages_for_user(user)
            
            if not unread_data:
                self.stdout.write(self.style.WARNING(f'No unread messages for user {user.username}'))
                return
            
            total_unread = sum(item['count'] for item in unread_data.values())
            self.stdout.write(f'User {user.username} has {total_unread} unread messages in {len(unread_data)} conversations')
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS('Would send digest email to: ' + user.email))
                return
            
            email_log = send_message_digest_to_user(user_id)
            
            if email_log and email_log.status == 'sent':
                self.stdout.write(self.style.SUCCESS(f'Digest sent to {user.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send digest to {user.email}'))
        
        else:
            # Send to all users
            if dry_run:
                from notifications.services.discussion_messages import get_unread_messages_for_user
                from accounts.models import User
                
                users = User.objects.filter(is_active=True).exclude(email='').exclude(email__isnull=True)
                would_send = 0
                
                for user in users:
                    unread_data = get_unread_messages_for_user(user)
                    if unread_data:
                        total_unread = sum(item['count'] for item in unread_data.values())
                        self.stdout.write(f'  Would send to {user.email}: {total_unread} unread messages')
                        would_send += 1
                
                self.stdout.write(self.style.SUCCESS(f'\nWould send {would_send} digest emails'))
                return
            
            self.stdout.write('Sending message digests to all users with unread messages...')
            
            results = send_all_pending_message_digests()
            
            self.stdout.write('')
            self.stdout.write(f'Users processed: {results["users_processed"]}')
            self.stdout.write(self.style.SUCCESS(f'Emails sent: {results["emails_sent"]}'))
            
            if results['emails_failed'] > 0:
                self.stdout.write(self.style.ERROR(f'Emails failed: {results["emails_failed"]}'))
            
            self.stdout.write(f'Users skipped (no unread): {results["users_skipped"]}')
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Message digest sending complete!'))
