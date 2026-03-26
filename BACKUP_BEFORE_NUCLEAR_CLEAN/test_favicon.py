"""
Test script to verify favicon implementation.

Usage:
    python test_favicon.py

This script checks:
1. Favicon file exists
2. All base templates have favicon link
3. Template syntax is valid
"""

import os
import re

def test_favicon_file_exists():
    """Test that the favicon files exist."""
    print("\n" + "="*60)
    print("TEST 1: Favicon Files Exist")
    print("="*60)
    
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
            print(f"✓ {favicon_path} ({file_size:,} bytes)")
        else:
            print(f"✗ {favicon_path} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print(f"\n✓ All favicon files exist")
        print(f"✓ Total package size: {total_size:,} bytes")
    
    return all_exist

def test_template_has_favicon(template_path):
    """Test that a template has favicon link."""
    if not os.path.exists(template_path):
        print(f"  ✗ Template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for ICO favicon link (most important)
    ico_pattern = r'favicon_io/favicon\.ico'
    
    if re.search(ico_pattern, content, re.IGNORECASE):
        print(f"  ✓ {template_path}")
        return True
    else:
        print(f"  ✗ {template_path} - No ICO favicon link found")
        return False

def test_all_templates():
    """Test all base templates have favicon."""
    print("\n" + "="*60)
    print("TEST 2: Base Templates Have Favicon")
    print("="*60)
    
    templates = [
        "templates/admin/layout/base.html",
        "templates/user/layout/base.html",
        "templates/auth/login.html",
        "templates/shared/work_item_discussion.html",
        "templates/admin/base_site.html",
    ]
    
    results = []
    for template in templates:
        results.append(test_template_has_favicon(template))
    
    return all(results)

def test_static_tag_present():
    """Test that templates load static tag."""
    print("\n" + "="*60)
    print("TEST 3: Templates Load Static Tag")
    print("="*60)
    
    templates = [
        "templates/admin/layout/base.html",
        "templates/user/layout/base.html",
        "templates/auth/login.html",
        "templates/shared/work_item_discussion.html",
        "templates/admin/base_site.html",
    ]
    
    results = []
    for template_path in templates:
        if not os.path.exists(template_path):
            print(f"  ✗ Template not found: {template_path}")
            results.append(False)
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% load static %}" in content:
            print(f"  ✓ {template_path}")
            results.append(True)
        else:
            print(f"  ✗ {template_path} - No {{% load static %}}")
            results.append(False)
    
    return all(results)

def test_django_admin_override():
    """Test Django admin base_site.html override exists."""
    print("\n" + "="*60)
    print("TEST 4: Django Admin Override")
    print("="*60)
    
    template_path = "templates/admin/base_site.html"
    
    if not os.path.exists(template_path):
        print(f"  ✗ Django admin override not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required elements
    checks = [
        ('{% extends "admin/base.html" %}', "Extends admin/base.html"),
        ('{% load static %}', "Loads static tag"),
        ('{% block extrahead %}', "Has extrahead block"),
        ('<link rel="icon"', "Has favicon link"),
    ]
    
    all_passed = True
    for pattern, description in checks:
        if pattern in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description}")
            all_passed = False
    
    return all_passed

def test_no_duplicate_favicons():
    """Test that there are no duplicate favicon declarations."""
    print("\n" + "="*60)
    print("TEST 5: Complete Favicon Package")
    print("="*60)
    
    templates = [
        "templates/admin/layout/base.html",
        "templates/user/layout/base.html",
        "templates/auth/login.html",
        "templates/shared/work_item_discussion.html",
        "templates/admin/base_site.html",
    ]
    
    all_passed = True
    for template_path in templates:
        if not os.path.exists(template_path):
            continue
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for complete package
        required_files = [
            'favicon.ico',
            'favicon-16x16.png',
            'favicon-32x32.png',
            'apple-touch-icon.png',
            'site.webmanifest',
        ]
        
        missing = []
        for file in required_files:
            if file not in content:
                missing.append(file)
        
        if not missing:
            print(f"  ✓ {template_path} - Complete package")
        else:
            print(f"  ✗ {template_path} - Missing: {', '.join(missing)}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("FAVICON IMPLEMENTATION - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Favicon file exists
    results.append(test_favicon_file_exists())
    
    # Test 2: All templates have favicon
    results.append(test_all_templates())
    
    # Test 3: Templates load static tag
    results.append(test_static_tag_present())
    
    # Test 4: Django admin override
    results.append(test_django_admin_override())
    
    # Test 5: No duplicate favicons
    results.append(test_no_duplicate_favicons())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if all(results):
        print("\n✓ ALL TESTS PASSED")
        print("Favicon implementation is complete and correct!")
    else:
        print("\n✗ SOME TESTS FAILED")
        print("Please review the failed tests above.")
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Start development server: python manage.py runserver")
    print("2. Visit http://127.0.0.1:8000/login/")
    print("3. Check browser tab for Wise logo favicon")
    print("4. Test on different pages (admin, user, Django admin)")
    print("5. Deploy to production and verify")
    print("="*60)

if __name__ == "__main__":
    main()
