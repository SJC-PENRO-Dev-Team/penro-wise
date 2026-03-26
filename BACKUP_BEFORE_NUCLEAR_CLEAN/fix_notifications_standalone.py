"""
Standalone script to fix notification URLs
Can be run directly if you have database access
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from notifications.models import Notification

print("\n" + "="*60)
print("FIXING NOTIFICATION URLS")
print("="*60 + "\n")

total_fixed = 0

# 1. Fix MESSAGE notifications
print("1. Fixing MESSAGE notifications...")
admin_msg = Notification.objects.filter(
    category='message',
    recipient__login_role='admin'
).exclude(action_url='/admin/discussions/').update(action_url='/admin/discussions/')
print(f"   Fixed {admin_msg} admin message notifications")
total_fixed += admin_msg

user_msg = Notification.objects.filter(
    category='message',
    recipient__login_role='user'
).exclude(action_url='/user/discussions/').update(action_url='/user/discussions/')
print(f"   Fixed {user_msg} user message notifications")
total_fixed += user_msg

# 2. Fix STATUS notifications
print("\n2. Fixing STATUS notifications...")
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
print(f"   Fixed {status_count} status notifications")
total_fixed += status_count

# 3. Fix SYSTEM notifications (workcycle-related)
print("\n3. Fixing SYSTEM workcycle notifications...")
admin_sys = Notification.objects.filter(
    category='system',
    recipient__login_role='admin',
    title__icontains='workcycle'
).exclude(action_url='/admin/workcycles/').update(action_url='/admin/workcycles/')
print(f"   Fixed {admin_sys} admin workcycle notifications")
total_fixed += admin_sys

user_sys = Notification.objects.filter(
    category='system',
    recipient__login_role='user',
    title__icontains='workcycle'
).exclude(action_url='/user/work-items/').update(action_url='/user/work-items/')
print(f"   Fixed {user_sys} user workcycle notifications")
total_fixed += user_sys

# 4. Fix PROFILE/ORGANIZATION notifications
print("\n4. Fixing PROFILE/ORGANIZATION notifications...")

# User profile notifications
profile_user = Notification.objects.filter(
    category='system',
    recipient__login_role='user',
    title__icontains='Profile'
).exclude(action_url='/user/profile/').update(action_url='/user/profile/')
print(f"   Fixed {profile_user} user profile notifications")
total_fixed += profile_user

# User organization notifications
org_user = Notification.objects.filter(
    category='system',
    recipient__login_role='user',
    title__icontains='Organization'
).exclude(action_url='/user/profile/').update(action_url='/user/profile/')
print(f"   Fixed {org_user} user organization notifications")
total_fixed += org_user

# Admin profile notifications
profile_admin = Notification.objects.filter(
    category='system',
    recipient__login_role='admin',
    title__icontains='Profile'
).exclude(action_url='/admin/users/').update(action_url='/admin/users/')
print(f"   Fixed {profile_admin} admin profile notifications")
total_fixed += profile_admin

# Admin organization notifications
org_admin = Notification.objects.filter(
    category='system',
    recipient__login_role='admin',
    title__icontains='Organization'
).exclude(action_url='/admin/users/').update(action_url='/admin/users/')
print(f"   Fixed {org_admin} admin organization notifications")
total_fixed += org_admin

# 5. Fix ASSIGNMENT notifications
print("\n5. Fixing ASSIGNMENT notifications...")
assignment = Notification.objects.filter(
    category='assignment',
    recipient__login_role='user'
).exclude(action_url='/user/work-items/').update(action_url='/user/work-items/')
print(f"   Fixed {assignment} assignment notifications")
total_fixed += assignment

# 6. Fix REVIEW notifications
print("\n6. Fixing REVIEW notifications...")
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
print(f"   Fixed {review_count} review notifications")
total_fixed += review_count

print("\n" + "="*60)
print(f"✅ COMPLETE: Fixed {total_fixed} notifications total")
print("="*60 + "\n")
