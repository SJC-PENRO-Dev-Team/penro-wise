"""
Quick fix for link ID 13 - set acceptance_status to 'accepted'
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment

print("=" * 80)
print("FIX: Link ID 13 Acceptance Status")
print("=" * 80)

try:
    link = WorkItemAttachment.objects.get(id=13)
    
    print(f"\nLink ID: {link.id}")
    print(f"Title: {link.link_title}")
    print(f"URL: {link.link_url}")
    print(f"Current Status: {link.acceptance_status}")
    
    if link.acceptance_status == 'accepted':
        print("\n✓ Link is already accepted!")
    else:
        print(f"\nUpdating status from '{link.acceptance_status}' to 'accepted'...")
        link.acceptance_status = 'accepted'
        link.save()
        print("✓ Updated successfully!")
        
        # Verify
        link.refresh_from_db()
        print(f"\nVerification:")
        print(f"  New status: {link.acceptance_status}")
        
        if link.acceptance_status == 'accepted':
            print("\n✓ Link should now be visible in File Manager at /admin/documents/files/21/")
        else:
            print("\n✗ Update failed!")
            
except WorkItemAttachment.DoesNotExist:
    print("\n✗ Link ID 13 not found!")

print("\n" + "=" * 80)
