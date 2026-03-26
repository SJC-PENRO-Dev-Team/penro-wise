"""
Fix broken profile image references in the database.
This script will:
1. Check all users with profile_image set
2. Verify if the file exists
3. Clear the profile_image field if file is missing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from accounts.models import User

print("Checking profile images...\n")

users_with_images = User.objects.filter(profile_image__isnull=False).exclude(profile_image='')
fixed_count = 0

for user in users_with_images:
    image_path = user.profile_image.name
    full_path = os.path.join('media', image_path)
    
    if not os.path.exists(full_path):
        print(f"✗ User {user.id} ({user.username}): Missing file '{image_path}'")
        print(f"  Clearing profile_image field...")
        user.profile_image = None
        user.save()
        fixed_count += 1
    else:
        print(f"✓ User {user.id} ({user.username}): OK")

print(f"\n{'='*50}")
print(f"Fixed {fixed_count} broken profile image reference(s)")
print(f"{'='*50}")
