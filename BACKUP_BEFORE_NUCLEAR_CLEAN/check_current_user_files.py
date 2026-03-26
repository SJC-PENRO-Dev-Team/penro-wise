#!/usr/bin/env python
"""
Check which user should have files
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment, User

print("="*60)
print("USERS AND THEIR FILE COUNTS")
print("="*60)

users = User.objects.filter(login_role='user')
for user in users:
    files = WorkItemAttachment.objects.filter(uploaded_by=user)
    print(f"\n{user.username}:")
    print(f"  Total: {files.count()}")
    print(f"  Pending: {files.filter(acceptance_status='pending').count()}")
    print(f"  Accepted: {files.filter(acceptance_status='accepted').count()}")
    print(f"  Rejected: {files.filter(acceptance_status='rejected').count()}")

print("\n" + "="*60)
print("RECOMMENDATION")
print("="*60)
print("If you're seeing all zeros, you're likely logged in as:")
print("  - kleinuser (0 files)")
print("  - markuser (0 files)")
print("\nTo see file stats, log in as:")
print("  - godwinuser (2 files, both accepted)")
