#!/usr/bin/env python
"""
Check if the submission_detail.html template has been updated correctly.
"""

template_path = 'templates/document_tracking/submission_detail.html'

print("=" * 80)
print("CHECKING TEMPLATE UPDATE")
print("=" * 80)

try:
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key indicators of the new design
    checks = {
        'Modern card layout': 'border-radius: 14px' in content,
        'Purple theme color': '#8b5cf6' in content,
        'Link modals': 'singleLinkModal' in content and 'groupedLinksModal' in content,
        'Timeline styles': 'dt-timeline' in content,
        'Back button': 'Back to My Submissions' in content,
        'Grouped links function': 'showGroupedLinksModal' in content,
        'API endpoint': '/admin/documents/files/grouped-links/' in content,
    }
    
    print(f"\nTemplate file: {template_path}")
    print(f"File size: {len(content)} characters")
    print("\nFeature checks:")
    
    all_passed = True
    for feature, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status} - {feature}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n" + "=" * 80)
        print("✓ TEMPLATE HAS BEEN UPDATED CORRECTLY")
        print("=" * 80)
        print("\nIf the page still shows the old design, try:")
        print("1. Hard refresh the browser (Ctrl+Shift+R or Cmd+Shift+R)")
        print("2. Clear browser cache")
        print("3. Restart Django development server")
        print("4. Check if you're viewing the correct URL: /documents/submission/12/")
        print("5. Open browser DevTools (F12) and check Console for errors")
    else:
        print("\n" + "=" * 80)
        print("✗ TEMPLATE UPDATE INCOMPLETE")
        print("=" * 80)
        print("\nSome features are missing. The template may need to be re-saved.")
    
except FileNotFoundError:
    print(f"\n✗ ERROR: Template file not found at {template_path}")
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")

print("\n" + "=" * 80)
