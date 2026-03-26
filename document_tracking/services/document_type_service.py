"""
Document Type Service

Handles document type management operations.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from document_tracking.models import DocumentType, Submission


def get_active_document_types():
    """
    Get all active document types ordered by display order.
    
    Returns:
        QuerySet: Active DocumentType instances
    """
    return DocumentType.objects.filter(is_active=True).order_by('order', 'name')


def get_all_document_types():
    """
    Get all document types (active and inactive).
    
    Returns:
        QuerySet: All DocumentType instances
    """
    return DocumentType.objects.all().order_by('order', 'name')


def reorder_document_types(type_ids):
    """
    Reorder document types based on a list of IDs.
    
    Args:
        type_ids: List of DocumentType IDs in desired order
    
    Returns:
        bool: True if successful
    
    Raises:
        ValidationError: If invalid IDs provided
    """
    with transaction.atomic():
        for index, type_id in enumerate(type_ids):
            try:
                doc_type = DocumentType.objects.get(id=type_id)
                doc_type.order = index
                doc_type.save()
            except DocumentType.DoesNotExist:
                raise ValidationError(f"Document type with ID {type_id} does not exist")
    
    return True


def can_delete_document_type(document_type_id):
    """
    Check if a document type can be safely deleted.
    
    A document type cannot be deleted if it has submissions.
    
    Args:
        document_type_id: DocumentType ID
    
    Returns:
        dict: {'can_delete': bool, 'reason': str, 'submission_count': int}
    """
    try:
        doc_type = DocumentType.objects.get(id=document_type_id)
    except DocumentType.DoesNotExist:
        return {
            'can_delete': False,
            'reason': 'Document type does not exist',
            'submission_count': 0
        }
    
    submission_count = Submission.objects.filter(doc_type=doc_type).count()
    
    if submission_count > 0:
        return {
            'can_delete': False,
            'reason': f'Cannot delete: {submission_count} submission(s) use this document type',
            'submission_count': submission_count
        }
    
    return {
        'can_delete': True,
        'reason': 'Can be safely deleted',
        'submission_count': 0
    }


def delete_document_type(document_type_id):
    """
    Delete a document type if it's safe to do so.
    
    Args:
        document_type_id: DocumentType ID
    
    Returns:
        bool: True if deleted successfully
    
    Raises:
        ValidationError: If document type cannot be deleted
    """
    check = can_delete_document_type(document_type_id)
    
    if not check['can_delete']:
        raise ValidationError(check['reason'])
    
    try:
        doc_type = DocumentType.objects.get(id=document_type_id)
        doc_type.delete()
        return True
    except DocumentType.DoesNotExist:
        raise ValidationError('Document type does not exist')


def toggle_document_type_status(document_type_id):
    """
    Toggle the active status of a document type.
    
    Args:
        document_type_id: DocumentType ID
    
    Returns:
        bool: New active status
    
    Raises:
        ValidationError: If document type doesn't exist
    """
    try:
        doc_type = DocumentType.objects.get(id=document_type_id)
        doc_type.is_active = not doc_type.is_active
        doc_type.save()
        return doc_type.is_active
    except DocumentType.DoesNotExist:
        raise ValidationError('Document type does not exist')


def get_document_type_stats(document_type_id):
    """
    Get statistics for a document type.
    
    Args:
        document_type_id: DocumentType ID
    
    Returns:
        dict: Statistics including submission count, tracking numbers used, etc.
    """
    try:
        doc_type = DocumentType.objects.get(id=document_type_id)
    except DocumentType.DoesNotExist:
        return None
    
    from datetime import datetime
    current_year = datetime.now().year
    
    # Get submission counts
    total_submissions = Submission.objects.filter(doc_type=doc_type).count()
    this_year_submissions = Submission.objects.filter(
        doc_type=doc_type,
        created_at__year=current_year
    ).count()
    
    # Get tracking number stats
    with_tracking = Submission.objects.filter(
        doc_type=doc_type,
        tracking_number__isnull=False
    ).count()
    
    # Get sequence info for current year
    from document_tracking.models import TrackingNumberSequence
    try:
        sequence = TrackingNumberSequence.objects.get(
            document_type=doc_type,
            year=current_year
        )
        last_serial = sequence.last_serial
    except TrackingNumberSequence.DoesNotExist:
        last_serial = 0
    
    return {
        'document_type': doc_type,
        'total_submissions': total_submissions,
        'this_year_submissions': this_year_submissions,
        'current_year_count': this_year_submissions,  # Alias for template compatibility
        'with_tracking_number': with_tracking,
        'without_tracking_number': total_submissions - with_tracking,
        'current_year_serial': last_serial,
        'next_tracking_number': doc_type.format_tracking_number(current_year, last_serial + 1),
        'can_delete': total_submissions == 0  # Can only delete if no submissions
    }
