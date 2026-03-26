"""
Upload favicon to Cloudinary and get the URL.
Run this script to upload favicon and get the direct URL.
"""
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)

print("=" * 70)
print("UPLOADING FAVICON TO CLOUDINARY")
print("=" * 70)

# Upload ICO file
try:
    print("\n1. Uploading favicon.ico...")
    result_ico = cloudinary.uploader.upload(
        "static/img/favicon_io/favicon.ico",
        public_id="favicon",
        resource_type="raw",
        overwrite=True
    )
    ico_url = result_ico['secure_url']
    print(f"   ✓ ICO uploaded: {ico_url}")
except Exception as e:
    print(f"   ✗ ICO upload failed: {e}")
    ico_url = None

# Upload PNG files
try:
    print("\n2. Uploading favicon-32x32.png...")
    result_png32 = cloudinary.uploader.upload(
        "static/img/favicon_io/favicon-32x32.png",
        public_id="favicon-32x32",
        overwrite=True
    )
    png32_url = result_png32['secure_url']
    print(f"   ✓ PNG 32x32 uploaded: {png32_url}")
except Exception as e:
    print(f"   ✗ PNG 32x32 upload failed: {e}")
    png32_url = None

try:
    print("\n3. Uploading favicon-16x16.png...")
    result_png16 = cloudinary.uploader.upload(
        "static/img/favicon_io/favicon-16x16.png",
        public_id="favicon-16x16",
        overwrite=True
    )
    png16_url = result_png16['secure_url']
    print(f"   ✓ PNG 16x16 uploaded: {png16_url}")
except Exception as e:
    print(f"   ✗ PNG 16x16 upload failed: {e}")
    png16_url = None

# Print template code
print("\n" + "=" * 70)
print("CLOUDINARY URLS - USE THESE IN TEMPLATES")
print("=" * 70)

if ico_url:
    print(f"\nICO URL:\n{ico_url}")
    
if png32_url:
    print(f"\nPNG 32x32 URL:\n{png32_url}")
    
if png16_url:
    print(f"\nPNG 16x16 URL:\n{png16_url}")

print("\n" + "=" * 70)
print("TEMPLATE CODE")
print("=" * 70)

if ico_url:
    print("\nAdd this to your templates:")
    print(f'<link rel="icon" href="{ico_url}" type="image/x-icon">')
    print(f'<link rel="shortcut icon" href="{ico_url}" type="image/x-icon">')

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("1. Copy the ICO URL above")
print("2. Update all 5 templates to use the Cloudinary URL")
print("3. Deploy to production")
print("4. Favicon will work immediately (no static files needed)")
print("=" * 70)
