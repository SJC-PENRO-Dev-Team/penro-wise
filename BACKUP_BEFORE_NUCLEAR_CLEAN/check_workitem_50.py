import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItem

wi = WorkItem.objects.filter(id=50).first()
if wi:
    print(f"Work Item 50 exists: YES")
    print(f"is_active: {wi.is_active}")
    print(f"status: {wi.status}")
    print(f"review_decision: {wi.review_decision}")
    print(f"owner: {wi.owner}")
    print(f"workcycle: {wi.workcycle}")
else:
    print("Work Item 50 does NOT exist")
