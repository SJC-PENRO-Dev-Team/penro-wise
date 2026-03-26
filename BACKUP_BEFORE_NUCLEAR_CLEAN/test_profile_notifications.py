"""
Test script to verify profile notification system
Run with: python manage.py shell < test_profile_notifications.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User
from notifications.models import Notification, EmailLog
from notifications.services.user_management import (
    notify_user_password_reset_by_admin,
    notify_user_password_changed,
    notify_admins_user_password_changed,
    notify_admins_user_profile_updated
)

print("=" * 80)
print("PROFILE NOTIFICATION SYSTEM TEST")
print("=" * 80)

# Get test users
try:
    admin_user = User.objects.filter(login_role='admin', is_active=True).first()
    regular_user = User.objects.filter(login_role='user', is_active=True).first()
    
    if not admin_user or not regular_user:
        print("\n❌ ERROR: Need at least one admin and one regular user for testing")
        exit(1)
    
    print(f"\n✅ Test Users Found:")
    print(f"   Admin: {admin_user.get_full_name() or admin_user.username} ({admin_user.email})")
    print(f"   User: {regular_user.get_full_name() or regular_user.username} ({regular_user.email})")
    
    # Count existing notifications and emails
    initial_notif_count = Notification.objects.count()
    initial_email_count = EmailLog.objects.count()
    
    print(f"\n📊 Initial Counts:")
    print(f"   Notifications: {initial_notif_count}")
    print(f"   Email Logs: {initial_email_count}")
    
    # Test 1: Admin resets user password
    print("\n" + "=" * 80)
    print("TEST 1: Admin Resets User Password")
    print("=" * 80)
    try:
        notify_user_password_reset_by_admin(
            user=regular_user,
            reset_by_admin=admin_user
        )
        print("✅ Password reset notification sent successfully")
        
        # Check notifications
        new_notifs = Notification.objects.filter(
            recipient=regular_user,
            title="Your Password Has Been Reset"
        )
        print(f"   In-app notifications created: {new_notifs.count()}")
        
        # Check emails
        new_emails = EmailLog.objects.filter(
            recipient=regular_user,
            email_type="password_reset"
        ).order_by('-created_at')
        print(f"   Email logs created: {new_emails.count()}")
        if new_emails.exists():
            latest = new_emails.first()
            print(f"   Latest email status: {latest.status}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 2: User changes own password
    print("\n" + "=" * 80)
    print("TEST 2: User Changes Own Password")
    print("=" * 80)
    try:
        notify_user_password_changed(regular_user)
        print("✅ User password change notification sent successfully")
        
        # Check notifications
        new_notifs = Notification.objects.filter(
            recipient=regular_user,
            title="Password Changed Successfully"
        )
        print(f"   In-app notifications to user: {new_notifs.count()}")
        
        # Check emails
        new_emails = EmailLog.objects.filter(
            recipient=regular_user,
            email_type="password_change"
        ).order_by('-created_at')
        print(f"   Email logs to user: {new_emails.count()}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 3: Notify admins of user password change
    print("\n" + "=" * 80)
    print("TEST 3: Notify Admins of User Password Change")
    print("=" * 80)
    try:
        notify_admins_user_password_changed(regular_user)
        print("✅ Admin notifications sent successfully")
        
        # Check notifications
        admin_notifs = Notification.objects.filter(
            recipient__login_role='admin',
            title__icontains="User Password Changed"
        )
        print(f"   In-app notifications to admins: {admin_notifs.count()}")
        
        # Check emails
        admin_emails = EmailLog.objects.filter(
            recipient__login_role='admin',
            email_type="password_change",
            sender=regular_user
        ).order_by('-created_at')
        print(f"   Email logs to admins: {admin_emails.count()}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Test 4: User updates profile
    print("\n" + "=" * 80)
    print("TEST 4: User Updates Own Profile")
    print("=" * 80)
    try:
        changed_fields = {
            'first_name': 'Test',
            'email': 'test@example.com'
        }
        notify_admins_user_profile_updated(
            user=regular_user,
            updated_by_user=regular_user,
            changed_fields=changed_fields
        )
        print("✅ Profile update notifications sent successfully")
        
        # Check notifications
        admin_notifs = Notification.objects.filter(
            recipient__login_role='admin',
            title__icontains="User Profile Updated"
        )
        print(f"   In-app notifications to admins: {admin_notifs.count()}")
        
        # Check emails
        admin_emails = EmailLog.objects.filter(
            recipient__login_role='admin',
            email_type="profile_update",
            sender=regular_user
        ).order_by('-created_at')
        print(f"   Email logs to admins: {admin_emails.count()}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    # Final counts
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    final_notif_count = Notification.objects.count()
    final_email_count = EmailLog.objects.count()
    
    print(f"\n📊 Final Counts:")
    print(f"   Notifications: {final_notif_count} (added: {final_notif_count - initial_notif_count})")
    print(f"   Email Logs: {final_email_count} (added: {final_email_count - initial_email_count})")
    
    # Check email statuses
    recent_emails = EmailLog.objects.order_by('-created_at')[:10]
    print(f"\n📧 Recent Email Statuses:")
    for email in recent_emails:
        status_icon = "✅" if email.status == "sent" else "❌" if email.status == "failed" else "⏳"
        print(f"   {status_icon} {email.email_type}: {email.subject} → {email.recipient_email} ({email.status})")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
