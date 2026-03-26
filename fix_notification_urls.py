"""
Quick script to fix message notification URLs.
Run with: python fix_notification_urls.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from notifications.models import Notification

# Get all message notifications
try:
    message_notifications = Notification.objects.filter(category='message')
    
    print(f"Found {message_notifications.count()} message notifications")
    
    updated_count = 0
    
    for notif in message_notifications:
        # Determine correct URL based on recipient role
        if notif.recipient.login_role == 'admin':
            correct_url = '/admin/discussions/'
        else:
            correct_url = '/user/discussions/'
        
        # Update if different
        if notif.action_url != correct_url:
            old_url = notif.action_url
            notif.action_url = correct_url
            notif.save(update_fields=['action_url'])
            updated_count += 1
            print(f"Updated notification {notif.id}: '{old_url}' -> '{correct_url}'")
    
    print(f"\n✓ Successfully updated {updated_count} message notification URLs")
    print(f"✓ Total message notifications: {message_notifications.count()}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure you have run migrations first:")
    print("  python manage.py migrate")
