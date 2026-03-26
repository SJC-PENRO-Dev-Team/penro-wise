"""
Check and fix admin notification URLs
Run with: python manage.py check_admin_notifications
"""

from django.core.management.base import BaseCommand
from notifications.models import Notification
from accounts.models import User


class Command(BaseCommand):
    help = 'Check and fix admin notification URLs'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("CHECKING ADMIN NOTIFICATIONS")
        self.stdout.write("="*60 + "\n")

        # Get all admin users
        admins = User.objects.filter(login_role='admin')
        self.stdout.write(f"Found {admins.count()} admin users\n")

        fixed_count = 0
        checked_count = 0

        for admin in admins:
            self.stdout.write(f"\n--- Admin: {admin.username} ---")
            
            # Get their notifications
            notifs = Notification.objects.filter(recipient=admin).order_by('-created_at')[:10]
            
            self.stdout.write(f"Latest 10 notifications:")
            for notif in notifs:
                checked_count += 1
                self.stdout.write(f"\n  ID: {notif.id}")
                self.stdout.write(f"  Category: {notif.category}")
                self.stdout.write(f"  Title: {notif.title}")
                self.stdout.write(f"  Current URL: '{notif.action_url}'")
                
                # Determine correct URL
                correct_url = None
                
                if notif.category == 'message':
                    correct_url = '/admin/discussions/'
                elif notif.category == 'status' and notif.work_item:
                    correct_url = f'/admin/work-items/{notif.work_item.id}/review/'
                elif notif.category == 'system':
                    correct_url = '/admin/workcycles/'
                
                if correct_url and notif.action_url != correct_url:
                    self.stdout.write(self.style.ERROR(f"  ❌ WRONG! Should be: '{correct_url}'"))
                    self.stdout.write(f"  Fixing...")
                    notif.action_url = correct_url
                    notif.save(update_fields=['action_url'])
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Fixed!"))
                elif correct_url:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Correct"))
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  No action URL needed"))

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"DONE: Checked {checked_count} notifications, fixed {fixed_count}"))
        self.stdout.write("="*60 + "\n")
