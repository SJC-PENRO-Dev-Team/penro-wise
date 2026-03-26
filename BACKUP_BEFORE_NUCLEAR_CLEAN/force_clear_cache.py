"""
Force clear all Django caches and verify template.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from django.core.cache import cache
from django.template import engines

print("\n=== FORCE CLEARING ALL CACHES ===")

# Clear Django cache
cache.clear()
print("✓ Django cache cleared")

# Clear template cache
for engine in engines.all():
    if hasattr(engine, 'engine'):
        engine.engine.template_loaders[0].reset()
        print(f"✓ Template cache cleared for {engine.name}")

# Verify template file exists and has correct content
template_path = 'templates/document_tracking/submission_detail.html'
if os.path.exists(template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for the new document type display
    if 'submission.doc_type.name' in content:
        print(f"✓ Template has NEW doc_type field")
    else:
        print(f"✗ Template missing NEW doc_type field")
        
    if 'REBUILT' in content:
        print(f"✓ Template has REBUILT marker")
    else:
        print(f"✗ Template missing REBUILT marker")
        
    # Count occurrences
    doc_type_count = content.count('submission.doc_type')
    print(f"✓ Found {doc_type_count} references to submission.doc_type")
    
    # Show a sample
    if 'submission.doc_type.name' in content:
        idx = content.find('submission.doc_type.name')
        sample = content[max(0, idx-50):idx+100]
        print(f"\nSample from template:")
        print(f"...{sample}...")
else:
    print(f"✗ Template file not found: {template_path}")

print("\n=== CACHE CLEARED - RESTART SERVER NOW ===\n")
