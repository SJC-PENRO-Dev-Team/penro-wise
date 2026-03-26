"""
Update all templates to use Cloudinary URL for favicon.
Run this after uploading favicon to Cloudinary.
"""

# PASTE YOUR CLOUDINARY URL HERE
CLOUDINARY_FAVICON_URL = "https://res.cloudinary.com/YOUR_CLOUD_NAME/raw/upload/v1234567890/favicon.ico"

# If the URL above is not set, exit
if "YOUR_CLOUD_NAME" in CLOUDINARY_FAVICON_URL:
    print("=" * 70)
    print("ERROR: Please set your Cloudinary URL first!")
    print("=" * 70)
    print("\n1. Upload favicon.ico to Cloudinary")
    print("2. Copy the secure URL")
    print("3. Paste it in this script (line 7)")
    print("4. Run the script again")
    print("\n" + "=" * 70)
    exit(1)

import re

templates = [
    "templates/admin/layout/base.html",
    "templates/user/layout/base.html",
    "templates/auth/login.html",
    "templates/shared/work_item_discussion.html",
    "templates/admin/base_site.html",
]

print("=" * 70)
print("UPDATING TEMPLATES WITH CLOUDINARY URL")
print("=" * 70)
print(f"\nCloudinary URL: {CLOUDINARY_FAVICON_URL}\n")

for template_path in templates:
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern to match favicon links
        pattern = r'<link rel="(?:icon|shortcut icon)"[^>]*href="[^"]*"[^>]*>'
        
        # New favicon link
        new_link = f'<link rel="icon" href="{CLOUDINARY_FAVICON_URL}" type="image/x-icon">'
        
        # Replace all favicon links
        updated_content = re.sub(pattern, new_link, content)
        
        # Write back
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✓ Updated: {template_path}")
    
    except Exception as e:
        print(f"✗ Failed: {template_path} - {e}")

print("\n" + "=" * 70)
print("DONE!")
print("=" * 70)
print("\nNext steps:")
print("1. Review the changes")
print("2. Commit: git add templates/")
print("3. Commit: git commit -m 'Use Cloudinary URL for favicon'")
print("4. Deploy: git push origin main")
print("=" * 70)
