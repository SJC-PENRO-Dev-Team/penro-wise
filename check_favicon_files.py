"""
Quick favicon verification script (no Django required).
"""
import os
import re

print("\n" + "="*70)
print("FAVICON IMPLEMENTATION VERIFICATION")
print("="*70)

# Test 1: Check favicon files
print("\n1. FAVICON FILES:")
print("-" * 70)

favicon_files = [
    "static/img/favicon_io/favicon.ico",
    "static/img/favicon_io/favicon-16x16.png",
    "static/img/favicon_io/favicon-32x32.png",
    "static/img/favicon_io/apple-touch-icon.png",
    "static/img/favicon_io/android-chrome-192x192.png",
    "static/img/favicon_io/android-chrome-512x512.png",
    "static/img/favicon_io/site.webmanifest",
]

all_exist = True
total_size = 0

for favicon_path in favicon_files:
    if os.path.exists(favicon_path):
        file_size = os.path.getsize(favicon_path)
        total_size += file_size
        print(f"   ✓ {os.path.basename(favicon_path):30} ({file_size:,} bytes)")
    else:
        print(f"   ✗ {os.path.basename(favicon_path):30} NOT FOUND")
        all_exist = False

if all_exist:
    print(f"\n   ✓ All 7 favicon files exist (Total: {total_size:,} bytes)")
else:
    print(f"\n   ✗ Some favicon files are missing!")

# Test 2: Check templates
print("\n2. TEMPLATE IMPLEMENTATION:")
print("-" * 70)

templates = [
    "templates/admin/layout/base.html",
    "templates/user/layout/base.html",
    "templates/auth/login.html",
    "templates/shared/work_item_discussion.html",
    "templates/admin/base_site.html",
]

all_templates_ok = True

for template_path in templates:
    if not os.path.exists(template_path):
        print(f"   ✗ {template_path:50} NOT FOUND")
        all_templates_ok = False
        continue
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for ICO favicon (most important)
    has_ico = 'favicon.ico' in content
    has_static = '{% load static %}' in content or '{% extends' in content
    
    if has_ico and has_static:
        print(f"   ✓ {os.path.basename(template_path):50} ICO favicon present")
    else:
        print(f"   ✗ {os.path.basename(template_path):50} Missing ICO or static tag")
        all_templates_ok = False

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if all_exist and all_templates_ok:
    print("   ✓ FAVICON IMPLEMENTATION COMPLETE!")
    print("\n   All favicon files exist and all templates are configured correctly.")
    print("   The ICO format will load immediately and prevent flicker.")
else:
    print("   ✗ ISSUES FOUND")
    print("\n   Please review the errors above.")

print("\n" + "="*70)
print("NEXT STEPS:")
print("="*70)
print("   1. Start dev server: python manage.py runserver")
print("   2. Visit: http://127.0.0.1:8000/login/")
print("   3. Check browser tab for Wise logo favicon")
print("   4. Navigate between pages - favicon should NOT flicker")
print("   5. Test on multiple browsers (Chrome, Firefox, Edge)")
print("   6. Deploy to production and verify")
print("="*70 + "\n")
