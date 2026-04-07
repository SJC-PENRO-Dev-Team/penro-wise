"""
Test Cloudinary configuration and connection.
Usage: python test_cloudinary.py
"""

import os
import sys

from dotenv import load_dotenv


load_dotenv()

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

print("=" * 60)
print("CLOUDINARY CONFIGURATION TEST")
print("=" * 60)
print(f"CLOUDINARY_CLOUD_NAME configured: {'YES' if CLOUD_NAME else 'NO'}")
print(f"CLOUDINARY_API_KEY configured: {'YES' if API_KEY else 'NO'}")
print(f"CLOUDINARY_API_SECRET configured: {'YES' if API_SECRET else 'NO'}")

if not CLOUD_NAME or not API_KEY or not API_SECRET:
    print("\nCloudinary credentials are incomplete.")
    sys.exit(1)

try:
    import cloudinary
    import cloudinary.api

    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=API_KEY,
        api_secret=API_SECRET,
        secure=True,
    )
    result = cloudinary.api.usage()
    print("\nConnection successful")
    print(f"Plan: {result.get('plan', 'N/A')}")
except Exception as error:
    print(f"\nConnection failed: {error}")
    sys.exit(1)
