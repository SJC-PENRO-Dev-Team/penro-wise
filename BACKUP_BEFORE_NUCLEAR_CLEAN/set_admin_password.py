#!/usr/bin/env python
"""
Set password for admin user in SQLite3 database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User

try:
    # Get the admin user
    admin_user = User.objects.get(username='admin')
    
    # Set password to 'admin'
    admin_user.set_password('admin')
    admin_user.login_role = 'admin'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    
    print("✓ Admin user password set to 'admin'")
    print("✓ Admin user configured with admin role")
    print("✓ Ready to login with username: admin, password: admin")
    
except User.DoesNotExist:
    print("❌ Admin user not found")
except Exception as e:
    print(f"❌ Error: {e}")