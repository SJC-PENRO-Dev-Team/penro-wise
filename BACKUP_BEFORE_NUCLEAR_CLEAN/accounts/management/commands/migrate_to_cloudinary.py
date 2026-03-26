"""
Management command to migrate existing local media files to Cloudinary.
Usage: python manage.py migrate_to_cloudinary
"""

import os
import glob
from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User, WorkItemAttachment
import cloudinary.uploader


class Command(BaseCommand):
    help = 'Migrate existing local media files to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually uploading',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No files will be uploaded'))
        
        # Migrate profile images
        self.stdout.write(self.style.SUCCESS('\n=== Migrating Profile Images ==='))
        self.migrate_profile_images(dry_run)
        
        # Migrate work item attachments
        self.stdout.write(self.style.SUCCESS('\n=== Migrating Work Item Attachments ==='))
        self.migrate_work_attachments(dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Migration complete!'))

    def find_local_file(self, base_path):
        """Find a local file by matching the base path (without extension)"""
        # Try exact match first
        if os.path.exists(base_path):
            return base_path
        
        # Try with common extensions
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.docx', '.xlsx', '.csv', '.txt']:
            full_path = base_path + ext
            if os.path.exists(full_path):
                return full_path
        
        # Try glob pattern to find any file with this base name
        pattern = base_path + '*'
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
        
        return None

    def migrate_profile_images(self, dry_run):
        """Migrate user profile images to Cloudinary"""
        users_with_images = User.objects.exclude(profile_image='').exclude(profile_image__isnull=True)
        total = users_with_images.count()
        
        self.stdout.write(f'Found {total} users with profile images')
        
        for idx, user in enumerate(users_with_images, 1):
            try:
                # Get the file name from the CloudinaryField
                image_name = str(user.profile_image)
                
                # Construct local file path (without extension)
                base_path = os.path.join(settings.BASE_DIR, 'media', image_name)
                
                # Find the actual file
                local_path = self.find_local_file(base_path)
                
                if not local_path:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[{idx}/{total}] ⚠️  File not found: {user.username} - {image_name}'
                        )
                    )
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f'[{idx}/{total}] Would upload: {user.username} - {os.path.basename(local_path)}'
                    )
                else:
                    # Upload to Cloudinary
                    result = cloudinary.uploader.upload(
                        local_path,
                        folder='profile_images',
                        public_id=f'user_{user.id}_{os.path.splitext(os.path.basename(local_path))[0]}',
                        resource_type='image',
                        overwrite=True
                    )
                    
                    # Update the model with Cloudinary public_id
                    user.profile_image = result['public_id']
                    user.save(update_fields=['profile_image'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{idx}/{total}] ✅ Uploaded: {user.username} - {result["secure_url"]}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'[{idx}/{total}] ❌ Error uploading {user.username}: {str(e)}'
                    )
                )

    def migrate_work_attachments(self, dry_run):
        """Migrate work item attachments to Cloudinary"""
        attachments = WorkItemAttachment.objects.exclude(file='').exclude(file__isnull=True)
        total = attachments.count()
        
        self.stdout.write(f'Found {total} work item attachments')
        
        for idx, attachment in enumerate(attachments, 1):
            try:
                # Get the file name from the CloudinaryField
                file_name = str(attachment.file)
                
                # Construct local file path (without extension)
                base_path = os.path.join(settings.BASE_DIR, 'media', file_name)
                
                # Find the actual file
                local_path = self.find_local_file(base_path)
                
                if not local_path:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[{idx}/{total}] ⚠️  File not found: Attachment #{attachment.id} - {file_name}'
                        )
                    )
                    continue
                
                if dry_run:
                    self.stdout.write(
                        f'[{idx}/{total}] Would upload: Attachment #{attachment.id} - {os.path.basename(local_path)}'
                    )
                else:
                    # Determine resource type based on file extension
                    file_ext = os.path.splitext(local_path)[1].lower()
                    resource_type = 'image' if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'] else 'raw'
                    
                    # Upload to Cloudinary
                    result = cloudinary.uploader.upload(
                        local_path,
                        folder='work_items',
                        public_id=f'attachment_{attachment.id}_{os.path.splitext(os.path.basename(local_path))[0]}',
                        resource_type=resource_type,
                        overwrite=True
                    )
                    
                    # Update the model with Cloudinary public_id
                    attachment.file = result['public_id']
                    attachment.save(update_fields=['file'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[{idx}/{total}] ✅ Uploaded: Attachment #{attachment.id} - {result["secure_url"]}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'[{idx}/{total}] ❌ Error uploading attachment #{attachment.id}: {str(e)}'
                    )
                )
