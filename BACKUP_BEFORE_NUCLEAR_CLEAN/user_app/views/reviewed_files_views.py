"""
Reviewed Files Views for Users
View-only pages for accepted and rejected files.
Users can only view their own files.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q

from accounts.models import WorkItemAttachment


@login_required
def user_accepted_files(request):
    """
    View user's own accepted files.
    View-only - no undo capability for users.
    """
    # Get only the current user's accepted files
    files = WorkItemAttachment.objects.filter(
        acceptance_status='accepted',
        work_item__owner=request.user
    ).select_related(
        'work_item',
        'work_item__workcycle',
        'reviewed_by'
    ).order_by('-accepted_at')
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        files = files.filter(
            Q(work_item__workcycle__title__icontains=search_query) |
            Q(file__icontains=search_query)
        )
    
    # Filter by attachment type
    attachment_type = request.GET.get('type', '')
    if attachment_type:
        files = files.filter(attachment_type=attachment_type)
    
    # Get counts for stats
    total_count = files.count()
    
    # Get attachment type choices for filter
    attachment_types = WorkItemAttachment.ATTACHMENT_TYPE_CHOICES
    
    context = {
        'files': files,
        'total_count': total_count,
        'search_query': search_query,
        'current_type': attachment_type,
        'attachment_types': attachment_types,
        'page_title': 'My Accepted Files',
        'status_type': 'accepted',
    }
    
    return render(request, 'user/page/reviewed_files.html', context)


@login_required
def user_rejected_files(request):
    """
    View user's own rejected files.
    View-only - shows countdown to auto-deletion.
    """
    # Get only the current user's rejected files
    files = WorkItemAttachment.objects.filter(
        acceptance_status='rejected',
        work_item__owner=request.user
    ).select_related(
        'work_item',
        'work_item__workcycle',
        'reviewed_by'
    ).order_by('-rejected_at')
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        files = files.filter(
            Q(work_item__workcycle__title__icontains=search_query) |
            Q(file__icontains=search_query)
        )
    
    # Filter by attachment type
    attachment_type = request.GET.get('type', '')
    if attachment_type:
        files = files.filter(attachment_type=attachment_type)
    
    # Get counts for stats
    total_count = files.count()
    
    # Get attachment type choices for filter
    attachment_types = WorkItemAttachment.ATTACHMENT_TYPE_CHOICES
    
    context = {
        'files': files,
        'total_count': total_count,
        'search_query': search_query,
        'current_type': attachment_type,
        'attachment_types': attachment_types,
        'page_title': 'My Rejected Files',
        'status_type': 'rejected',
    }
    
    return render(request, 'user/page/reviewed_files.html', context)
