"""
Check attachment 130 in detail.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import WorkItemAttachment

# Get attachment 130
att = WorkItemAttachment.objects.get(id=130)

print("="*60)
print("ATTACHMENT 130 DETAILS")
print("="*60)
print(f"ID: {att.id}")
print(f"Folder: {att.folder}")
print(f"Attachment Type: {att.attachment_type}")
print(f"\nFile field:")
print(f"  att.file: {att.file}")
print(f"  att.file.name: {att.file.name if att.file else 'None'}")
print(f"  bool(att.file): {bool(att.file)}")
print(f"\nLink fields:")
print(f"  att.link_url: {att.link_url}")
print(f"  att.link_title: {att.link_title}")
print(f"  bool(att.link_url): {bool(att.link_url)}")
print(f"\nMethods:")
print(f"  att.is_link(): {att.is_link()}")
print(f"  att.is_file(): {att.is_file()}")
print(f"  att.get_filename(): {att.get_filename()}")
print(f"\nUploaded:")
print(f"  By: {att.uploaded_by}")
print(f"  At: {att.uploaded_at}")

print("\n" + "="*60)
print("ISSUE DIAGNOSIS")
print("="*60)

if att.file and att.link_url:
    print("❌ PROBLEM: Attachment has BOTH file and link_url!")
    print("   This violates the model's clean() validation.")
    print("   The attachment should have EITHER file OR link_url, not both.")
elif att.link_url:
    print("✓ OK: This is a link attachment (link_url is set, file is not)")
elif att.file:
    print("✓ OK: This is a file attachment (file is set, link_url is not)")
else:
    print("❌ PROBLEM: Attachment has NEITHER file nor link_url!")
