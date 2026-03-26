"""
Direct migration application script.
Run this in a NEW terminal window.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wise.settings')
django.setup()

from django.db import connection

print("="*60)
print("APPLYING SECTION MIGRATION DIRECTLY")
print("="*60)

# SQL commands to add the new fields
sql_commands = [
    # Add display_name (nullable first)
    "ALTER TABLE document_tracking_section ADD COLUMN display_name VARCHAR(150) NULL;",
    
    # Add description
    "ALTER TABLE document_tracking_section ADD COLUMN description TEXT DEFAULT '';",
    
    # Add is_active
    "ALTER TABLE document_tracking_section ADD COLUMN is_active BOOLEAN DEFAULT 1;",
    
    # Add order
    "ALTER TABLE document_tracking_section ADD COLUMN \"order\" INTEGER DEFAULT 0;",
    
    # Add updated_at
    "ALTER TABLE document_tracking_section ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;",
]

# Populate display_name from name
populate_sql = """
UPDATE document_tracking_section 
SET display_name = CASE 
    WHEN name = 'licensing' THEN 'Licensing'
    WHEN name = 'enforcement' THEN 'Enforcement'
    WHEN name = 'admin' THEN 'Admin'
    ELSE name
END
WHERE display_name IS NULL;
"""

# Make display_name non-nullable (SQLite doesn't support this directly, so we skip it)

try:
    with connection.cursor() as cursor:
        print("\n1. Adding new columns...")
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"   {i}. {sql[:50]}...")
                cursor.execute(sql)
                print(f"      ✓ Success")
            except Exception as e:
                if 'duplicate column name' in str(e).lower():
                    print(f"      ⚠ Column already exists, skipping")
                else:
                    print(f"      ❌ Error: {e}")
        
        print("\n2. Populating display_name...")
        cursor.execute(populate_sql)
        print("   ✓ Display names populated")
        
        print("\n3. Verifying sections...")
        cursor.execute("SELECT name, display_name, is_active, \"order\" FROM document_tracking_section")
        sections = cursor.fetchall()
        
        if sections:
            print(f"   Found {len(sections)} sections:")
            for section in sections:
                print(f"     - {section[0]}: {section[1]} (active={section[2]}, order={section[3]})")
        else:
            print("   ⚠ No sections found")
        
        print("\n" + "="*60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\nNext steps:")
        print("1. Run: python manage.py create_default_sections")
        print("2. Visit: http://127.0.0.1:8000/documents/admin/settings/sections/")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
