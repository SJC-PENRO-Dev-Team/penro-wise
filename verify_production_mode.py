"""
Verify environment-driven database, media, and email configuration.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


print("=" * 60)
print("ENV CONFIGURATION VERIFICATION")
print("=" * 60)

database_url = os.getenv("DATABASE_URL", "").strip()
if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
    print("DATABASE: PostgreSQL")
    print("  DATABASE_URL is configured")
else:
    print("DATABASE: SQLite3")
    print("  DATABASE_URL is not configured")

print()

cloudinary_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
cloudinary_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
cloudinary_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()

if cloudinary_name and cloudinary_key and cloudinary_secret:
    print("MEDIA STORAGE: Cloudinary")
    print("  Cloudinary credentials are configured")
else:
    print("MEDIA STORAGE: Local File System")
    print("  Cloudinary credentials are not configured")

print()

brevo_key = os.getenv("BREVO_API_KEY", "").strip()
email_password = os.getenv("EMAIL_HOST_PASSWORD", "").strip()
if brevo_key:
    print("EMAIL: Brevo API")
    print("  BREVO_API_KEY is configured")
elif email_password:
    print("EMAIL: SMTP")
    print("  EMAIL_HOST_PASSWORD is configured")
else:
    print("EMAIL: Not configured")

print()
print("=" * 60)
print("NEXT STEPS")
print("=" * 60)
print("1. Restart Django after changing .env values")
print("2. Database and media storage follow the active env configuration")
print("3. Static files remain on the Django staticfiles pipeline")
