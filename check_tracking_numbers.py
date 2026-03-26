#!/usr/bin/env python3
"""
Check existing tracking numbers to understand the format and structure.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'penro_project.settings')
django.setup()

from document_tracking.models import Submission, DocumentType

def check_tracking_numbers():
    """Check existing tracking numbers and document types"""
    
    print("🔍 Checking Tracking Numbers and Document Types")
    print("=" * 60)
    
    # Check document types
    print("📋 Document Types:")
    doc_types = DocumentType.objects.all()
    for doc_type in doc_types:
        print(f"   - {doc_type.name} ({doc_type.prefix})")
    
    print(f"\n📊 Total Document Types: {doc_types.count()}")
    
    # Check submissions with tracking numbers
    print("\n📋 Submissions with Tracking Numbers:")
    submissions = Submission.objects.filter(tracking_number__isnull=False).order_by('tracking_number')
    
    for submission in submissions:
        print(f"   - {submission.tracking_number} | {submission.title[:50]}... | {submission.get_status_display()}")
    
    print(f"\n📊 Total Submissions with Tracking Numbers: {submissions.count()}")
    
    # Check submissions without tracking numbers
    no_tracking = Submission.objects.filter(tracking_number__isnull=True).count()
    print(f"📊 Submissions without Tracking Numbers: {no_tracking}")
    
    # Analyze tracking number patterns
    if submissions.exists():
        print("\n📋 Tracking Number Analysis:")
        tracking_numbers = [s.tracking_number for s in submissions]
        
        # Extract prefixes
        prefixes = set()
        years = set()
        for tn in tracking_numbers:
            if '-' in tn:
                parts = tn.split('-')
                if len(parts) >= 2:
                    prefixes.add(parts[0])
                    try:
                        years.add(int(parts[1]))
                    except ValueError:
                        pass
        
        print(f"   - Prefixes found: {sorted(prefixes)}")
        print(f"   - Years found: {sorted(years)}")
        print(f"   - Example format: {tracking_numbers[0] if tracking_numbers else 'None'}")

if __name__ == '__main__':
    try:
        check_tracking_numbers()
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()