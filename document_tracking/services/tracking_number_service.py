"""
Tracking Number Service

Handles generation, validation, and management of tracking numbers.
Format: PREFIX-YEAR-SERIAL (e.g., MEM-2026-001)
"""
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
import re

from document_tracking.models import DocumentType, TrackingNumberSequence, Submission


def generate_tracking_number(document_type, year=None, serial=None):
    """
    Generate a tracking number for a document type.
    Respects document_type.reset_policy (none, monthly, yearly).
    
    Args:
        document_type: DocumentType instance
        year: Year for tracking number (defaults to current year)
        serial: Manual serial number (optional, for manual mode)
    
    Returns:
        str: Formatted tracking number (e.g., "MEM-2026-000000000001")
    
    Raises:
        ValidationError: If tracking number already exists or invalid serial
    """
    if year is None:
        year = datetime.now().year
    
    # Validate year
    if not (2000 <= year <= 2100):
        raise ValidationError(f"Invalid year: {year}")
    
    with transaction.atomic():
        if serial is None:
            # Auto-generate serial number based on reset_policy
            month = datetime.now().month if document_type.reset_policy == 'monthly' else None
            serial = document_type.get_next_serial(year, month)
        else:
            # Validate manual serial
            if not isinstance(serial, int) or serial < 1:
                raise ValidationError("Serial number must be a positive integer")
            
            # Update sequence if this serial is higher than last_serial
            month = datetime.now().month if document_type.reset_policy == 'monthly' else None
            
            # For continuous sequence (reset_policy='none'), use year=1
            seq_year = 1 if document_type.reset_policy == 'none' else year
            
            sequence, created = TrackingNumberSequence.objects.select_for_update().get_or_create(
                document_type=document_type,
                year=seq_year,
                month=month,
                defaults={'last_serial': serial}
            )
            
            if serial > sequence.last_serial:
                sequence.last_serial = serial
                sequence.save()
        
        # Format tracking number
        tracking_number = document_type.format_tracking_number(year, serial)
        
        # Validate uniqueness
        if not is_tracking_number_unique(tracking_number):
            raise ValidationError(f"Tracking number {tracking_number} already exists")
        
        return tracking_number


def validate_tracking_number(tracking_number, exclude_submission_id=None):
    """
    Validate a tracking number format and uniqueness.
    
    Args:
        tracking_number: Tracking number string to validate
        exclude_submission_id: Submission ID to exclude from uniqueness check
    
    Returns:
        dict: {'valid': bool, 'errors': list, 'parsed': dict}
    """
    errors = []
    parsed = None
    
    # Parse tracking number
    try:
        parsed = parse_tracking_number(tracking_number)
    except ValidationError as e:
        errors.append(str(e))
        return {'valid': False, 'errors': errors, 'parsed': None}
    
    # Check uniqueness
    if not is_tracking_number_unique(tracking_number, exclude_submission_id):
        errors.append(f"Tracking number {tracking_number} already exists")
    
    # Validate prefix exists
    if not DocumentType.objects.filter(prefix=parsed['prefix']).exists():
        errors.append(f"Unknown document type prefix: {parsed['prefix']}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'parsed': parsed
    }


def parse_tracking_number(tracking_number):
    """
    Parse a tracking number into its components.
    
    Args:
        tracking_number: Tracking number string (e.g., "MEM-2026-001")
    
    Returns:
        dict: {'prefix': str, 'year': int, 'serial': int}
    
    Raises:
        ValidationError: If format is invalid
    """
    if not tracking_number:
        raise ValidationError("Tracking number cannot be empty")
    
    # Expected format: PREFIX-YEAR-SERIAL (12 digits)
    pattern = r'^([A-Z]{2,5})-(\d{4})-(\d{12})$'
    match = re.match(pattern, tracking_number.upper())
    
    if not match:
        raise ValidationError(
            "Invalid tracking number format. Expected: PREFIX-YEAR-SERIAL (e.g., MEM-2026-001)"
        )
    
    prefix, year_str, serial_str = match.groups()
    
    try:
        year = int(year_str)
        serial = int(serial_str)
    except ValueError:
        raise ValidationError("Year and serial must be numeric")
    
    # Validate year range
    if not (2000 <= year <= 2100):
        raise ValidationError(f"Year must be between 2000 and 2100, got {year}")
    
    # Validate serial
    if serial < 1:
        raise ValidationError("Serial number must be positive")
    
    return {
        'prefix': prefix,
        'year': year,
        'serial': serial
    }


def is_tracking_number_unique(tracking_number, exclude_submission_id=None):
    """
    Check if a tracking number is unique.
    
    Args:
        tracking_number: Tracking number to check
        exclude_submission_id: Submission ID to exclude from check
    
    Returns:
        bool: True if unique, False if already exists
    """
    query = Submission.objects.filter(tracking_number=tracking_number)
    
    if exclude_submission_id:
        query = query.exclude(id=exclude_submission_id)
    
    return not query.exists()


def get_next_serial(document_type, year=None):
    """
    Get the next available serial number for a document type and year.
    
    Args:
        document_type: DocumentType instance
        year: Year (defaults to current year)
    
    Returns:
        int: Next serial number
    """
    if year is None:
        year = datetime.now().year
    
    return document_type.get_next_serial(year)


def format_tracking_number_preview(document_type, year=None):
    """
    Generate a preview of what the next tracking number will look like.
    
    Args:
        document_type: DocumentType instance
        year: Year (defaults to current year)
    
    Returns:
        str: Preview tracking number (e.g., "MEM-2026-XXX")
    """
    if year is None:
        year = datetime.now().year
    
    return f"{document_type.prefix}-{year}-XXX"


def assign_tracking_number(submission, document_type=None, year=None, serial=None):
    """
    Assign a tracking number to a submission.
    
    Args:
        submission: Submission instance
        document_type: DocumentType instance (defaults to submission.doc_type)
        year: Year (defaults to current year)
        serial: Manual serial number (optional)
    
    Returns:
        str: Assigned tracking number
    
    Raises:
        ValidationError: If tracking number cannot be assigned
    """
    if submission.tracking_number and submission.tracking_locked:
        raise ValidationError("Tracking number is locked and cannot be changed")
    
    if document_type is None:
        document_type = submission.doc_type
    
    if document_type is None:
        raise ValidationError(
            "No document type selected. Please select a document type from the dropdown menu."
        )
    
    # Generate tracking number
    tracking_number = generate_tracking_number(document_type, year, serial)
    
    # Assign to submission
    submission.tracking_number = tracking_number
    submission.doc_type = document_type
    submission.tracking_locked = True
    submission.save()
    
    return tracking_number


def reset_annual_sequences(year=None):
    """
    Reset all sequences for document types with reset_annually=True.
    
    This should be run at the start of each year.
    
    Args:
        year: Year to reset (defaults to current year)
    
    Returns:
        int: Number of sequences reset
    """
    if year is None:
        year = datetime.now().year
    
    # Get document types that reset annually
    document_types = DocumentType.objects.filter(reset_annually=True)
    
    reset_count = 0
    for doc_type in document_types:
        # Create new sequence for the year (if it doesn't exist)
        sequence, created = TrackingNumberSequence.objects.get_or_create(
            document_type=doc_type,
            year=year,
            defaults={'last_serial': 0}
        )
        
        if created:
            reset_count += 1
    
    return reset_count
