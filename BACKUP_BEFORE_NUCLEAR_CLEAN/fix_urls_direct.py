"""
Direct SQL update to fix notification URLs.
Run with: python fix_urls_direct.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.db import connection

# Direct SQL update
with connection.cursor() as cursor:
    # Update admin message notifications
    cursor.execute("""
        UPDATE notifications_notification 
        SET action_url = '/admin/discussions/'
        WHERE category = 'message' 
        AND recipient_id IN (
            SELECT id FROM accounts_user WHERE login_role = 'admin'
        )
    """)
    admin_updated = cursor.rowcount
    
    # Update user message notifications
    cursor.execute("""
        UPDATE notifications_notification 
        SET action_url = '/user/discussions/'
        WHERE category = 'message' 
        AND recipient_id IN (
            SELECT id FROM accounts_user WHERE login_role = 'user'
        )
    """)
    user_updated = cursor.rowcount

print(f"✓ Updated {admin_updated} admin message notifications to /admin/discussions/")
print(f"✓ Updated {user_updated} user message notifications to /user/discussions/")
print(f"✓ Total updated: {admin_updated + user_updated}")
