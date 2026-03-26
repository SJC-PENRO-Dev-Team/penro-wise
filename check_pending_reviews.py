#!/usr/bin/env python
"""
Check pending review counts for work items
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItem

# Get active work items
items = WorkItem.objects.filter(is_active=True, workcycle__is_active=True)

print(f"Total active items: {items.count()}")
print(f"Status=done: {items.filter(status='done').count()}")
print(f"Review=pending: {items.filter(review_decision='pending').count()}")
print(f"Status=done AND Review=pending: {items.filter(status='done', review_decision='pending').count()}")

print("\n" + "="*60)
print("Sample items with status='done':")
print("="*60)
for item in items.filter(status='done')[:10]:
    print(f"  - {item.workcycle.title}")
    print(f"    Owner: {item.owner.username}")
    print(f"    Status: {item.status}")
    print(f"    Review: {item.review_decision}")
    print(f"    Submitted: {item.submitted_at}")
    print()

print("\n" + "="*60)
print("All items with review_decision='pending' (any status):")
print("="*60)
for item in items.filter(review_decision='pending')[:10]:
    print(f"  - {item.workcycle.title}")
    print(f"    Owner: {item.owner.username}")
    print(f"    Status: {item.status}")
    print(f"    Review: {item.review_decision}")
    print(f"    Submitted: {item.submitted_at}")
    print()

print("\n" + "="*60)
print("SUMMARY:")
print("="*60)
print(f"Items that are submitted AND pending review: {items.filter(status='done', review_decision='pending').count()}")
print(f"Items that are submitted but already reviewed: {items.filter(status='done').exclude(review_decision='pending').count()}")
print(f"Items NOT submitted but have pending status: {items.filter(review_decision='pending').exclude(status='done').count()}")
print("\nCONCLUSION:")
if items.filter(status='done', review_decision='pending').count() == 0:
    print("✓ The count is correct - there are NO items awaiting review.")
    print("  The submitted item was already approved/reviewed.")
    print("  The 'pending' items haven't been submitted yet.")
else:
    print(f"✓ There are {items.filter(status='done', review_decision='pending').count()} items awaiting review.")
