"""
Reviewed Files Views
Pages for viewing accepted and rejected files.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.utils.timezone import now, localdate
from datetime import timedelta

from accounts.models import WorkItemAttachment


@login_required
def accepted_files_list(request):
    """
    View recently accepted files.
    Admins can undo acceptance, users can only view.
    Default: shows files accepted today. Can filter by period.
    """
    today = localdate()
    
    # Period filter (default: today)
    period = request.GET.get('period', 'today')
    
    # Base queryset
    files = WorkItemAttachment.objects.filter(
        acceptance_status='accepted'
    ).select_related(
        'work_item',
        'work_item__owner',
        'work_item__workcycle',
        'uploaded_by',
        'reviewed_by'
    ).order_by('-accepted_at')
    
    # Apply period filter
    if period == 'today':
        files = files.filter(accepted_at__date=today)
        period_label = 'Today'
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        files = files.filter(accepted_at__date__gte=week_start)
        period_label = 'This Week'
    elif period == 'month':
        files = files.filter(
            accepted_at__year=today.year,
            accepted_at__month=today.month
        )
        period_label = 'This Month'
    elif period == 'all':
        period_label = 'All Time'
    else:
        # Default to today
        files = files.filter(accepted_at__date=today)
        period_label = 'Today'
        period = 'today'
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        files = files.filter(
            Q(work_item__owner__first_name__icontains=search_query) |
            Q(work_item__owner__last_name__icontains=search_query) |
            Q(work_item__owner__username__icontains=search_query) |
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
        'page_title': 'Accepted Files',
        'status_type': 'accepted',
        'is_admin': request.user.login_role == 'admin',
        'current_period': period,
        'period_label': period_label,
    }
    
    return render(request, 'admin/page/reviewed_files.html', context)


@login_required
def rejected_files_list(request):
    """
    View recently rejected files.
    Admins can undo rejection, users can only view.
    Shows countdown to auto-deletion.
    Default: shows files rejected today. Can filter by period.
    """
    today = localdate()
    
    # Period filter (default: today)
    period = request.GET.get('period', 'today')
    
    # Base queryset
    files = WorkItemAttachment.objects.filter(
        acceptance_status='rejected'
    ).select_related(
        'work_item',
        'work_item__owner',
        'work_item__workcycle',
        'uploaded_by',
        'reviewed_by'
    ).order_by('-rejected_at')
    
    # Apply period filter
    if period == 'today':
        files = files.filter(rejected_at__date=today)
        period_label = 'Today'
    elif period == 'week':
        week_start = today - timedelta(days=today.weekday())
        files = files.filter(rejected_at__date__gte=week_start)
        period_label = 'This Week'
    elif period == 'month':
        files = files.filter(
            rejected_at__year=today.year,
            rejected_at__month=today.month
        )
        period_label = 'This Month'
    elif period == 'all':
        period_label = 'All Time'
    else:
        # Default to today
        files = files.filter(rejected_at__date=today)
        period_label = 'Today'
        period = 'today'
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        files = files.filter(
            Q(work_item__owner__first_name__icontains=search_query) |
            Q(work_item__owner__last_name__icontains=search_query) |
            Q(work_item__owner__username__icontains=search_query) |
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
        'page_title': 'Rejected Files',
        'status_type': 'rejected',
        'is_admin': request.user.login_role == 'admin',
        'current_period': period,
        'period_label': period_label,
    }
    
    return render(request, 'admin/page/reviewed_files.html', context)
