#!/usr/bin/env python3
"""
Script to remove organization modal and related code from profile.html
"""

def cleanup_profile_template():
    """Remove organization modal HTML and JavaScript from profile template"""
    
    with open('templates/shared/profile.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and mark sections to remove
    in_org_modal = False
    in_org_js = False
    cleaned_lines = []
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Start of organization modal HTML (around line 444)
        if '<!-- ORGANIZATION SETUP MODAL -->' in line:
            in_org_modal = True
            print(f"Found organization modal start at line {line_num}")
            continue
        
        # End of organization modal HTML (before CHANGE PROFILE IMAGE MODAL)
        if in_org_modal and '<!-- CHANGE PROFILE IMAGE MODAL -->' in line:
            in_org_modal = False
            print(f"Found organization modal end at line {line_num}")
            cleaned_lines.append(line)
            continue
        
        # Start of organization JavaScript (around line 757)
        if 'ORGANIZATION SETUP MODAL' in line and '/*' in line:
            in_org_js = True
            print(f"Found organization JS start at line {line_num}")
            continue
        
        # End of organization JavaScript (before IMAGE PREVIEW section)
        if in_org_js and 'IMAGE PREVIEW' in line and '/*' in line:
            in_org_js = False
            print(f"Found organization JS end at line {line_num}")
            cleaned_lines.append(line)
            continue
        
        # Skip lines in organization sections
        if in_org_modal or in_org_js:
            continue
        
        # Keep all other lines
        cleaned_lines.append(line)
    
    # Write cleaned content back
    with open('templates/shared/profile.html', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"\n✅ Cleaned profile template")
    print(f"   Original lines: {len(lines)}")
    print(f"   Cleaned lines: {len(cleaned_lines)}")
    print(f"   Removed lines: {len(lines) - len(cleaned_lines)}")

if __name__ == '__main__':
    cleanup_profile_template()
