#!/usr/bin/env python
"""
Check file stats for users
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, User

# Get all users
users = User.objects.filter(login_role='user')

print("="*60)
print("FILE STATS BY USER")
print("="*60)

for user in users:
    user_files = WorkItemAttachment.objects.filter(uploaded_by=user)
    
    print(f"\nUser: {user.username}")
    print(f"  Total files: {user_files.count()}")
    print(f"  Pending: {user_files.filter(acceptance_status='pending').count()}")
    print(f"  Accepted: {user_files.filter(acceptance_status='accepted').count()}")
    print(f"  Rejected: {user_files.filter(acceptance_status='rejected').count()}")
    
    if user_files.exists():
        print(f"  Sample files:")
        for file in user_files[:3]:
            print(f"    - {file.get_filename()} (status: {file.acceptance_status})")

print("\n" + "="*60)
print("ALL FILES IN SYSTEM")
print("="*60)
all_files = WorkItemAttachment.objects.all()
print(f"Total files: {all_files.count()}")
print(f"Pending: {all_files.filter(acceptance_status='pending').count()}")
print(f"Accepted: {all_files.filter(acceptance_status='accepted').count()}")
print(f"Rejected: {all_files.filter(acceptance_status='rejected').count()}")
