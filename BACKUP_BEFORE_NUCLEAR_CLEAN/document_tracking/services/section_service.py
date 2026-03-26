"""
Section/Department management service.

Handles CRUD operations and business logic for sections.
"""
from document_tracking.models import Section, Submission
from django.db.models import Count


def get_all_sections():
    """Get all sections ordered by order field."""
    return Section.objects.all().order_by('order', 'name')


def get_active_sections():
    """Get only active sections."""
    return Section.objects.filter(is_active=True).order_by('order', 'name')


def get_section_stats(section_id):
    """
    Get statistics for a section.
    
    Args:
        section_id: Section ID
        
    Returns:
        Dictionary with statistics
    """
    section = Section.objects.get(id=section_id)
    
    stats = {
        'total_submissions': Submission.objects.filter(assigned_section=section).count(),
        'pending_submissions': Submission.objects.filter(
            assigned_section=section,
            status__in=['received', 'under_review', 'for_compliance']
        ).count(),
        'approved_submissions': Submission.objects.filter(
            assigned_section=section,
            status='approved'
        ).count(),
        'officers_count': section.officers.count(),
    }
    
    return stats


def can_delete_section(section_id):
    """
    Check if section can be deleted (no submissions assigned).
    
    Args:
        section_id: Section ID
        
    Returns:
        True if can delete, False otherwise
    """
    section = Section.objects.get(id=section_id)
    return not Submission.objects.filter(assigned_section=section).exists()


def delete_section(section_id):
    """
    Delete section if allowed.
    
    Args:
        section_id: Section ID
        
    Raises:
        ValueError: If section has assigned submissions
    """
    if not can_delete_section(section_id):
        raise ValueError("Cannot delete section with assigned submissions")
    
    section = Section.objects.get(id=section_id)
    section.delete()


def reorder_sections(section_ids):
    """
    Reorder sections based on provided list of IDs.
    
    Args:
        section_ids: List of section IDs in desired order
    """
    for index, section_id in enumerate(section_ids):
        Section.objects.filter(id=section_id).update(order=index)
