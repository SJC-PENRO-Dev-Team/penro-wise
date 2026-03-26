import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User

users_with_images = User.objects.filter(profile_image__isnull=False).exclude(profile_image='')

print(f"\nFound {users_with_images.count()} users with profile images:\n")

for user in users_with_images:
    image_path = user.profile_image.name if user.profile_image else 'None'
    full_path = f"media/{image_path}" if image_path else 'None'
    exists = os.path.exists(full_path) if image_path else False
    status = "✓ EXISTS" if exists else "✗ MISSING"
    print(f"{status} | User {user.id}: {user.username}")
    print(f"         DB Path: {image_path}")
    if not exists and image_path:
        print(f"         Full Path: {full_path}")
    print()
