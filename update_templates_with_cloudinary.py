"""
Update templates to use the Cloudinary favicon URL from the environment.
"""

import os
import re

from dotenv import load_dotenv


load_dotenv()

CLOUDINARY_FAVICON_URL = os.getenv("CLOUDINARY_FAVICON_URL", "").strip()

if not CLOUDINARY_FAVICON_URL:
    print("=" * 70)
    print("ERROR: CLOUDINARY_FAVICON_URL is not set")
    print("=" * 70)
    print("\n1. Upload favicon.ico to Cloudinary")
    print("2. Set CLOUDINARY_FAVICON_URL in .env")
    print("3. Run this script again")
    raise SystemExit(1)

templates = [
    "templates/admin/layout/base.html",
    "templates/user/layout/base.html",
    "templates/auth/login.html",
    "templates/shared/work_item_discussion.html",
    "templates/admin/base_site.html",
]

for template_path in templates:
    with open(template_path, "r", encoding="utf-8") as file_handle:
        content = file_handle.read()

    pattern = r'<link rel="(?:icon|shortcut icon)"[^>]*href="[^"]*"[^>]*>'
    new_link = f'<link rel="icon" href="{CLOUDINARY_FAVICON_URL}" type="image/x-icon">'
    updated_content = re.sub(pattern, new_link, content)

    with open(template_path, "w", encoding="utf-8") as file_handle:
        file_handle.write(updated_content)

    print(f"Updated: {template_path}")
