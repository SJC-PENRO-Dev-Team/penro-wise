"""
Test if the file preview system can handle Cloudinary-stored files.
"""

import os

from dotenv import load_dotenv

load_dotenv()

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "penro_project.settings")
django.setup()

from accounts.models import WorkItemAttachment
from django.conf import settings


def test_cloudinary_files():
    print("=" * 60)
    print("CLOUDINARY FILE PREVIEW TEST")
    print("=" * 60)
    print(f"\nDEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}")
    print(f"CLOUD_NAME: {getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'N/A')}")

    attachments = WorkItemAttachment.objects.all()[:5]
    print(f"\nSample attachment count: {attachments.count()}")

    for attachment in attachments:
        print(f"\nFile: {attachment.file.name}")
        try:
            print(f"URL available: {'YES' if attachment.file.url else 'NO'}")
        except Exception as error:
            print(f"URL error: {error}")


if __name__ == "__main__":
    test_cloudinary_files()
