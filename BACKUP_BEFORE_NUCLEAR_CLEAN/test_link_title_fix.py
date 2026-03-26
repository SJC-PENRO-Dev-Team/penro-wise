"""
Test script to verify the link title duplication bug is fixed.
This simulates the POST data that would be sent when creating links.
"""

# Simulate the POST data
post_data = {
    'link_title': 'SAMPLE',
    'link_1': 'https://drive.google.com/spreadsheets/d/1f2O1dYZeer_qKZDpcXzhd07k-Vt76twO/edit',
    'link_2': 'https://docs.google.com/document/d/abc123',
}

# OLD CODE (buggy)
print("=== OLD CODE (BUGGY) ===")
links_old = []
for key in post_data:
    if key.startswith("link_"):
        link = post_data.get(key, "").strip()
        if link:
            links_old.append(link)

print(f"Links extracted: {len(links_old)}")
for i, link in enumerate(links_old, 1):
    print(f"  Link {i}: {link}")

print()

# NEW CODE (fixed)
print("=== NEW CODE (FIXED) ===")
link_title = post_data.get("link_title", "").strip()
links_new = []
for key in post_data:
    if key.startswith("link_") and key != "link_title":
        link = post_data.get(key, "").strip()
        # Additional validation: ensure it's a valid URL, not the title
        if link and link != link_title:
            links_new.append(link)

print(f"Title: {link_title}")
print(f"Links extracted: {len(links_new)}")
for i, link in enumerate(links_new, 1):
    print(f"  Link {i}: {link}")

print()
print("=== RESULT ===")
if 'SAMPLE' in links_old:
    print("❌ OLD CODE: Title was incorrectly added as a link!")
else:
    print("✓ OLD CODE: Title was not added (unexpected)")

if 'SAMPLE' not in links_new:
    print("✓ NEW CODE: Title is correctly excluded from links!")
else:
    print("❌ NEW CODE: Title was incorrectly added as a link (bug still exists)")
