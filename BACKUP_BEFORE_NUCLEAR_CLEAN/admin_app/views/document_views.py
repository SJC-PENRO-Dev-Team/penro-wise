from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncDate
from datetime import timedelta

from accounts.models import WorkItemAttachment, WorkCycle, User


@staff_member_required
def admin_documents(request):
    """
    Enhanced Documents Dashboard with comprehensive analytics.
    """
    current_year = now().year
    current_month = now().month
    today = now().date()
    
    # Base queryset
    all_attachments = WorkItemAttachment.objects.all()
    
    # =====================================================
    # CORE METRICS
    # =====================================================
    total_files = all_attachments.count()
    files_this_year = all_attachments.filter(uploaded_at__year=current_year).count()
    files_this_month = all_attachments.filter(
        uploaded_at__year=current_year,
        uploaded_at__month=current_month
    ).count()
    files_today = all_attachments.filter(uploaded_at__date=today).count()
    
    # =====================================================
    # FILE STATUS BREAKDOWN
    # =====================================================
    status_breakdown = {
        'pending': all_attachments.filter(acceptance_status='pending').count(),
        'accepted': all_attachments.filter(acceptance_status='accepted').count(),
        'rejected': all_attachments.filter(acceptance_status='rejected').count(),
    }
    
    # =====================================================
    # FILES BY TYPE
    # =====================================================
    files_by_type = list(
        all_attachments
        .values('attachment_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Map type codes to display names
    type_display_map = dict(WorkItemAttachment.ATTACHMENT_TYPE_CHOICES)
    for item in files_by_type:
        item['display_name'] = type_display_map.get(item['attachment_type'], item['attachment_type'])
    
    # =====================================================
    # MONTHLY UPLOAD TREND (Last 6 months)
    # =====================================================
    six_months_ago = now() - timedelta(days=180)
    monthly_uploads = list(
        all_attachments
        .filter(uploaded_at__gte=six_months_ago)
        .annotate(month=TruncMonth('uploaded_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # =====================================================
    # TOP UPLOADERS (Last 30 days)
    # =====================================================
    thirty_days_ago = now() - timedelta(days=30)
    top_uploaders = list(
        all_attachments
        .filter(uploaded_at__gte=thirty_days_ago, uploaded_by__isnull=False)
        .values('uploaded_by__id', 'uploaded_by__first_name', 'uploaded_by__last_name', 'uploaded_by__username')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    
    # =====================================================
    # FILES BY WORKCYCLE (Top 5 active)
    # =====================================================
    files_by_workcycle = list(
        all_attachments
        .filter(work_item__workcycle__is_active=True)
        .values('work_item__workcycle__id', 'work_item__workcycle__title')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    
    # =====================================================
    # FILES BY DEPARTMENT
    # =====================================================
    # Get files grouped by the uploader's department
    files_by_department = list(
        all_attachments
        .filter(uploaded_by__department__isnull=False)
        .values('uploaded_by__department__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # =====================================================
    # RECENT ACTIVITY (Last 10 uploads)
    # =====================================================
    recent_uploads = list(
        all_attachments
        .select_related('uploaded_by', 'work_item__workcycle')
        .order_by('-uploaded_at')[:10]
    )
    
    # =====================================================
    # STORAGE INSIGHTS
    # =====================================================
    # Count files that might be missing (we'll check this in template/JS)
    pending_review_count = all_attachments.filter(acceptance_status='pending').count()
    
    # Files expiring soon (rejected files within 24h of deletion)
    expiring_soon = all_attachments.filter(
        acceptance_status='rejected',
        rejection_expires_at__lte=now() + timedelta(hours=24),
        rejection_expires_at__gt=now()
    ).count()
    
    # =====================================================
    # YEAR OPTIONS FOR NAVIGATION
    # =====================================================
    years = (
        WorkItemAttachment.objects
        .values_list("uploaded_at__year", flat=True)
        .distinct()
        .order_by("-uploaded_at__year")
    )

    return render(
        request,
        "admin/page/documents_dashboard.html",
        {
            # Core metrics
            "total_files": total_files,
            "files_this_year": files_this_year,
            "files_this_month": files_this_month,
            "files_today": files_today,
            
            # Status breakdown
            "status_breakdown": status_breakdown,
            
            # Analytics data
            "files_by_type": files_by_type,
            "monthly_uploads": monthly_uploads,
            "top_uploaders": top_uploaders,
            "files_by_workcycle": files_by_workcycle,
            "files_by_department": files_by_department,
            "recent_uploads": recent_uploads,
            
            # Alerts
            "pending_review_count": pending_review_count,
            "expiring_soon": expiring_soon,
            
            # Navigation
            "years": years,
            "now": now(),
            "current_year": current_year,
        }
    )
