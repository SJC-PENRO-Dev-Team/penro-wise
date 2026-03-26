"""
Fix all notification URLs in the database
Run with: python manage.py fix_all_notification_urls
"""

from django.core.management.base import BaseCommand
from django.db import connection
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Fix all notification URLs in the database'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("FIXING ALL NOTIFICATION URLS")
        self.stdout.write("="*60 + "\n")

        total_fixed = 0

        # Fix MESSAGE notifications
        self.stdout.write("\n1. Fixing MESSAGE notifications...")
        
        # Admin message notifications
        admin_message_count = Notification.objects.filter(
            category='message',
            recipient__login_role='admin'
        ).exclude(action_url='/admin/discussions/').update(
            action_url='/admin/discussions/'
        )
        self.stdout.write(f"   Fixed {admin_message_count} admin message notifications")
        total_fixed += admin_message_count
        
        # User message notifications
        user_message_count = Notification.objects.filter(
            category='message',
            recipient__login_role='user'
        ).exclude(action_url='/user/discussions/').update(
            action_url='/user/discussions/'
        )
        self.stdout.write(f"   Fixed {user_message_count} user message notifications")
        total_fixed += user_message_count

        # Fix STATUS notifications (admin only)
        self.stdout.write("\n2. Fixing STATUS notifications...")
        status_notifs = Notification.objects.filter(
            category='status',
            recipient__login_role='admin',
            work_item__isnull=False
        )
        status_count = 0
        for notif in status_notifs:
            correct_url = f'/admin/work-items/{notif.work_item.id}/review/'
            if notif.action_url != correct_url:
                notif.action_url = correct_url
                notif.save(update_fields=['action_url'])
                status_count += 1
        self.stdout.write(f"   Fixed {status_count} status notifications")
        total_fixed += status_count

        # Fix SYSTEM notifications
        self.stdout.write("\n3. Fixing SYSTEM notifications...")
        
        # Admin system notifications
        admin_system_count = Notification.objects.filter(
            category='system',
            recipient__login_role='admin'
        ).exclude(action_url='/admin/workcycles/').update(
            action_url='/admin/workcycles/'
        )
        self.stdout.write(f"   Fixed {admin_system_count} admin system notifications")
        total_fixed += admin_system_count
        
        # User system notifications
        user_system_count = Notification.objects.filter(
            category='system',
            recipient__login_role='user'
        ).exclude(action_url='/user/work-items/').update(
            action_url='/user/work-items/'
        )
        self.stdout.write(f"   Fixed {user_system_count} user system notifications")
        total_fixed += user_system_count

        # Fix profile/organization notifications
        self.stdout.write("\n4. Fixing PROFILE/ORGANIZATION notifications...")
        
        # Profile update notifications for users
        profile_user_count = Notification.objects.filter(
            category='system',
            recipient__login_role='user',
            title__icontains='Profile'
        ).exclude(action_url='/user/profile/').update(
            action_url='/user/profile/'
        )
        self.stdout.write(f"   Fixed {profile_user_count} user profile notifications")
        total_fixed += profile_user_count
        
        # Organization update notifications for users
        org_user_count = Notification.objects.filter(
            category='system',
            recipient__login_role='user',
            title__icontains='Organization'
        ).exclude(action_url='/user/profile/').update(
            action_url='/user/profile/'
        )
        self.stdout.write(f"   Fixed {org_user_count} user organization notifications")
        total_fixed += org_user_count
        
        # Profile update notifications for admins (should go to their own profile or users list)
        profile_admin_count = Notification.objects.filter(
            category='system',
            recipient__login_role='admin',
            title__icontains='Profile'
        ).exclude(action_url='/admin/users/').update(
            action_url='/admin/users/'
        )
        self.stdout.write(f"   Fixed {profile_admin_count} admin profile notifications")
        total_fixed += profile_admin_count

        # Fix ASSIGNMENT notifications (user only)
        self.stdout.write("\n5. Fixing ASSIGNMENT notifications...")
        assignment_count = Notification.objects.filter(
            category='assignment',
            recipient__login_role='user'
        ).exclude(action_url='/user/work-items/').update(
            action_url='/user/work-items/'
        )
        self.stdout.write(f"   Fixed {assignment_count} assignment notifications")
        total_fixed += assignment_count

        # Fix REVIEW notifications (user only)
        self.stdout.write("\n6. Fixing REVIEW notifications...")
        review_notifs = Notification.objects.filter(
            category='review',
            recipient__login_role='user',
            work_item__isnull=False
        )
        review_count = 0
        for notif in review_notifs:
            correct_url = f'/user/work-items/{notif.work_item.id}/'
            if notif.action_url != correct_url:
                notif.action_url = correct_url
                notif.save(update_fields=['action_url'])
                review_count += 1
        self.stdout.write(f"   Fixed {review_count} review notifications")
        total_fixed += review_count

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"✅ COMPLETE: Fixed {total_fixed} notifications total"))
        self.stdout.write("="*60 + "\n")
