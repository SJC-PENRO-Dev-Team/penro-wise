"""
Check and fix admin notification URLs
Run with: python manage.py shell < check_and_fix_admin_notifs.py
"""

from notifications.models import Notification
from accounts.models import User

print("\n" + "="*60)
print("CHECKING ADMIN NOTIFICATIONS")
print("="*60 + "\n")

# Get all admin users
admins = User.objects.filter(login_role='admin')
print(f"Found {admins.count()} admin users\n")

for admin in admins:
    print(f"\n--- Admin: {admin.username} ---")
    
    # Get their notifications
    notifs = Notification.objects.filter(recipient=admin).order_by('-created_at')[:10]
    
    print(f"Latest 10 notifications:")
    for notif in notifs:
        print(f"\n  ID: {notif.id}")
        print(f"  Category: {notif.category}")
        print(f"  Title: {notif.title}")
        print(f"  Current URL: '{notif.action_url}'")
        
        # Determine correct URL
        correct_url = None
        
        if notif.category == 'message':
            correct_url = '/admin/discussions/'
        elif notif.category == 'status' and notif.work_item:
            correct_url = f'/admin/work-items/{notif.work_item.id}/review/'
        elif notif.category == 'system':
            correct_url = '/admin/workcycles/'
        
        if correct_url and notif.action_url != correct_url:
            print(f"  ❌ WRONG! Should be: '{correct_url}'")
            print(f"  Fixing...")
            notif.action_url = correct_url
            notif.save(update_fields=['action_url'])
            print(f"  ✅ Fixed!")
        elif correct_url:
            print(f"  ✅ Correct")
        else:
            print(f"  ⚠️  No action URL needed")

print("\n" + "="*60)
print("DONE")
print("="*60 + "\n")
