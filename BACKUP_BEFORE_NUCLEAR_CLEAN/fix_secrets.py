#!/usr/bin/env python3
"""
Fix secrets in documentation files to prevent GitHub secret scanning issues.
"""

import os
import re

# Files to fix
files_to_fix = [
    'DEPLOYMENT_READINESS_CHECK.md',
    'READY_TO_DEPLOY.txt'
]

# Replacements to make
replacements = [
    ('[REDACTED_CLOUDINARY_API_KEY]', '[YOUR_CLOUDINARY_API_KEY]'),
    ('[REDACTED_CLOUDINARY_CLOUD_NAME]', '[YOUR_CLOUDINARY_CLOUD_NAME]'),
    ('[REDACTED_BREVO_EMAIL_USER]', '[YOUR_BREVO_EMAIL_USER]'),
]

def fix_file(filepath):
    """Fix secrets in a single file."""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        # Read file content
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply replacements
        for old_value, new_value in replacements:
            content = content.replace(old_value, new_value)
        
        # Write back if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed secrets in: {filepath}")
            return True
        else:
            print(f"ℹ️  No changes needed in: {filepath}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False

def main():
    """Main function to fix all files."""
    print("🔒 Fixing secrets in documentation files...")
    print("=" * 50)
    
    fixed_count = 0
    
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed_count += 1
    
    print("=" * 50)
    print(f"✅ Fixed {fixed_count} file(s)")
    
    if fixed_count > 0:
        print("\n🚀 Next steps:")
        print("1. git add .")
        print("2. git commit -m 'fix: remove secrets from documentation files'")
        print("3. git push origin main")
    else:
        print("\n✅ No secrets found - you're good to go!")

if __name__ == '__main__':
    main()