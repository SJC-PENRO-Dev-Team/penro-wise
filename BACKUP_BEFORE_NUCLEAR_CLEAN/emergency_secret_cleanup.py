#!/usr/bin/env python3
"""
EMERGENCY SECRET CLEANUP - Remove ALL hardcoded secrets from the repository
"""

import os
import re
import glob

# All files that might contain secrets
files_to_clean = [
    '.env',
    'DEPLOYMENT_READINESS_CHECK.md',
    'READY_TO_DEPLOY.txt',
    'POSTGRES_CLOUDINARY_ENABLED.md',
    'QUICK_REFERENCE_POSTGRES_CLOUDINARY.md',
    'test_cloudinary_postgres.py',
    'CLOUDINARY_SETUP_COMPLETE.md',
    'CLOUDINARY_MIGRATION_SUMMARY.md',
    'test_cloudinary.py',
    'POSTGRES_CLOUDINARY_SWITCH_COMPLETE.md'
]

# Add all markdown and text files
files_to_clean.extend(glob.glob('*.md'))
files_to_clean.extend(glob.glob('*.txt'))
files_to_clean.extend(glob.glob('*.py'))

# Remove duplicates
files_to_clean = list(set(files_to_clean))

# Secrets to replace
secrets_to_replace = [
    # Cloudinary secrets
    ('[REDACTED_CLOUDINARY_API_KEY]', '[REDACTED_CLOUDINARY_API_KEY]'),
    ('[REDACTED_CLOUDINARY_CLOUD_NAME]', '[REDACTED_CLOUDINARY_CLOUD_NAME]'),
    ('[REDACTED_CLOUDINARY_API_SECRET]', '[REDACTED_CLOUDINARY_API_SECRET]'),
    
    # Brevo/Email secrets
    ('[REDACTED_BREVO_API_KEY]', '[REDACTED_BREVO_API_KEY]'),
    ('[REDACTED_BREVO_SMTP_PASSWORD]', '[REDACTED_BREVO_SMTP_PASSWORD]'),
    ('[REDACTED_BREVO_EMAIL_USER]', '[REDACTED_BREVO_EMAIL_USER]'),
    
    # Database secrets
    ('[REDACTED_DATABASE_URL]', '[REDACTED_DATABASE_URL]'),
    ('[REDACTED_DB_USER]', '[REDACTED_DB_USER]'),
    ('[REDACTED_DB_PASSWORD]', '[REDACTED_DB_PASSWORD]'),
    ('[REDACTED_DB_HOST]', '[REDACTED_DB_HOST]'),
    ('[REDACTED_DB_NAME]', '[REDACTED_DB_NAME]'),
    
    # Django secret
    ('[REDACTED_DJANGO_SECRET_KEY]', '[REDACTED_DJANGO_SECRET_KEY]'),
]

def clean_file(filepath):
    """Clean secrets from a single file."""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for secret, replacement in secrets_to_replace:
            content = content.replace(secret, replacement)
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔒 CLEANED: {filepath}")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ ERROR cleaning {filepath}: {str(e)}")
        return False

def main():
    """Main cleanup function."""
    print("🚨 EMERGENCY SECRET CLEANUP - REMOVING ALL HARDCODED SECRETS")
    print("=" * 60)
    
    cleaned_count = 0
    
    for filepath in files_to_clean:
        if clean_file(filepath):
            cleaned_count += 1
    
    print("=" * 60)
    print(f"🔒 CLEANED {cleaned_count} files")
    
    # Create safe .env template
    safe_env_content = """# Django Settings
DEBUG=True
SECRET_KEY=[YOUR_DJANGO_SECRET_KEY]

# Database Configuration
# For LOCAL DEVELOPMENT: Comment out DATABASE_URL to use SQLite3
# For PRODUCTION: Set your PostgreSQL URL
# DATABASE_URL=[YOUR_POSTGRESQL_URL]

# Site URL
SITE_URL=http://localhost:8000

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1

# CSRF Trusted Origins (comma-separated)
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1

# Email Configuration (Brevo API)
# BREVO_API_KEY=[YOUR_BREVO_API_KEY]
DEFAULT_FROM_EMAIL=Your App <noreply@yourapp.com>

# Cloudinary Configuration (Media File Storage)
# For LOCAL DEVELOPMENT: Comment out to use local file storage
# For PRODUCTION: Set your Cloudinary credentials
# CLOUDINARY_CLOUD_NAME=[YOUR_CLOUDINARY_CLOUD_NAME]
# CLOUDINARY_API_KEY=[YOUR_CLOUDINARY_API_KEY]
# CLOUDINARY_API_SECRET=[YOUR_CLOUDINARY_API_SECRET]
"""
    
    with open('.env', 'w') as f:
        f.write(safe_env_content)
    
    print("✅ Created safe .env template")
    print("\n🚨 CRITICAL SECURITY ACTIONS NEEDED:")
    print("1. IMMEDIATELY rotate ALL these credentials:")
    print("   - Cloudinary API keys")
    print("   - Brevo API keys") 
    print("   - Database passwords")
    print("   - Django secret key")
    print("2. Update your production environment variables")
    print("3. Never commit .env files again")
    print("\n🔥 Ready to commit clean files!")

if __name__ == '__main__':
    main()