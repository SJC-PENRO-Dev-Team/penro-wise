"""
Assign admin user to Workforces Department
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User, WorkforcesDepartment

try:
    admin = User.objects.get(username='admin')
    dept = WorkforcesDepartment.objects.first()
    
    if not dept:
        print("[ERROR] No department found. Run create_default_department.py first")
    else:
        admin.department = dept
        admin.save()
        print("[OK] Admin assigned to department")
        print(f"   User: {admin.username}")
        print(f"   Department: {dept.name}")
except User.DoesNotExist:
    print("[ERROR] Admin user not found")
