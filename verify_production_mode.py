"""
Verify Production Mode Configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*60)
print("PRODUCTION MODE VERIFICATION")
print("="*60)

# Check Database
database_url = os.getenv('DATABASE_URL')
if database_url and 'postgresql' in database_url:
    print("✓ DATABASE: PostgreSQL (PRODUCTION)")
    print(f"  Connection: {database_url[:50]}...")
else:
    print("✗ DATABASE: SQLite3 (LOCAL)")

print()

# Check Cloudinary
cloudinary_name = os.getenv('CLOUDINARY_CLOUD_NAME')
cloudinary_key = os.getenv('CLOUDINARY_API_KEY')
cloudinary_secret = os.getenv('CLOUDINARY_API_SECRET')

if cloudinary_name and cloudinary_key and cloudinary_secret:
    print("✓ MEDIA STORAGE: Cloudinary (PRODUCTION)")
    print(f"  Cloud Name: {cloudinary_name}")
    print(f"  API Key: {cloudinary_key}")
else:
    print("✗ MEDIA STORAGE: Local File System (LOCAL)")

print()

# Check Email
brevo_key = os.getenv('BREVO_API_KEY')
if brevo_key:
    print("✓ EMAIL: Brevo API (PRODUCTION)")
    print(f"  API Key: {brevo_key[:20]}...")
else:
    print("✗ EMAIL: Not configured")

print()
print("="*60)
print("NEXT STEPS:")
print("="*60)
print("1. Restart Django server: python manage.py runserver")
print("2. All file uploads will go to Cloudinary")
print("3. All data will be stored in PostgreSQL")
print("4. Profile images will load from Cloudinary")
print()
print("To switch back to LOCAL mode:")
print("- Comment out DATABASE_URL")
print("- Comment out CLOUDINARY_* variables")
