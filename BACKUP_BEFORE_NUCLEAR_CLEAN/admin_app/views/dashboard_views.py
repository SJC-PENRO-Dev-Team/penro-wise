"""
Admin Dashboard Views
Provides comprehensive analytics and overview for administrators.
"""
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.shortcuts import render
from django.utils import timezone

from accounts.models import User, WorkCycle, WorkItem, WorkItemAttachment, WorkforcesDepartment
from document_tracking.models import Submission


@login_required
def main_dashboard(request):
    """
    Main admin dashboard - central hub showing all system modules.
    """
    # Document Tracking Stats
    doc_tracking_stats = {
        'total_submissions': Submission.objects.count(),
        'pending_tracking': Submission.objects.filter(status='pending_tracking').count(),
        'under_review': Submission.objects.filter(status='under_review').count(),
        'approved': Submission.objects.filter(status='approved').count(),
    }
    
    # Workstate Stats
    workstate_stats = {
        'active_workcycles': WorkCycle.objects.filter(is_active=True).count(),
        'total_work_items': WorkItem.objects.filter(is_active=True, workcycle__is_active=True).count(),
        'pending_reviews': WorkItem.objects.filter(
            review_decision='pending',
            status='done',
            workcycle__is_active=True
        ).count(),
    }
    
    # File Manager Stats
    from structure.models import DocumentFolder
    file_manager_stats = {
        'total_files': WorkItemAttachment.objects.filter(attachment_type__in=['FILE', 'matrix_a', 'matrix_b', 'matrix_c']).count(),
        'total_folders': DocumentFolder.objects.count(),
        'total_links': WorkItemAttachment.objects.filter(attachment_type='LINK').count(),
    }
    
    return render(
        request,
        'admin/page/main_dashboard.html',
        {
            'doc_tracking_stats': doc_tracking_stats,
            'workstate_stats': workstate_stats,
            'file_manager_stats': file_manager_stats,
        },
    )


@login_required
def workstate_overview(request):
    """
    Workstate overview with comprehensive analytics.
    """
    now = timezone.now()
    
    # =====================================================
    # WORK CYCLE STATS
    # =====================================================
    active_workcycles = WorkCycle.objects.filter(is_active=True)
    
    # Lifecycle breakdown
    workcycle_stats = {
        "total_active": active_workcycles.count(),
        "ongoing": 0,
        "due_soon": 0,
        "lapsed": 0,
    }
    
    for wc in active_workcycles:
        state = wc.lifecycle_state
        if state in workcycle_stats:
            workcycle_stats[state] += 1
    
    # =====================================================
    # WORK ITEM STATS
    # =====================================================
    active_work_items = WorkItem.objects.filter(
        is_active=True,
        workcycle__is_active=True
    )
    
    work_item_stats = {
        "total": active_work_items.count(),
        "not_started": active_work_items.filter(status="not_started").count(),
        "working_on_it": active_work_items.filter(status="working_on_it").count(),
        "done": active_work_items.filter(status="done").count(),
    }
    
    # Review stats
    review_stats = {
        "pending": active_work_items.filter(review_decision="pending", status="done").count(),
        "approved": active_work_items.filter(review_decision="approved").count(),
        "revision": active_work_items.filter(review_decision="revision").count(),
    }
    
    # =====================================================
    # USER STATS
    # =====================================================
    user_stats = {
        "total": User.objects.filter(is_active=True).count(),
        "admins": User.objects.filter(is_active=True, login_role="admin").count(),
        "users": User.objects.filter(is_active=True, login_role="user").count(),
        "unassigned": User.objects.filter(
            is_active=True,
            department__isnull=True
        ).count(),
    }
    
    # =====================================================
    # FILE STATS
    # =====================================================
    file_stats = {
        "total": WorkItemAttachment.objects.count(),
        "pending": WorkItemAttachment.objects.filter(acceptance_status="pending").count(),
        "accepted": WorkItemAttachment.objects.filter(acceptance_status="accepted").count(),
        "rejected": WorkItemAttachment.objects.filter(acceptance_status="rejected").count(),
    }
    
    # =====================================================
    # RECENT ACTIVITY
    # =====================================================
    recent_submissions = (
        WorkItem.objects
        .filter(status="done", submitted_at__isnull=False)
        .select_related("owner", "workcycle")
        .order_by("-submitted_at")[:5]
    )
    
    pending_reviews = (
        WorkItem.objects
        .filter(
            review_decision="pending",
            status="done",
            workcycle__is_active=True
        )
        .select_related("owner", "workcycle")
        .order_by("-submitted_at")[:5]
    )
    
    # =====================================================
    # UPCOMING DEADLINES
    # =====================================================
    upcoming_deadlines = (
        WorkCycle.objects
        .filter(is_active=True, due_at__gte=now)
        .order_by("due_at")[:5]
    )
    
    # =====================================================
    # DEPARTMENT STATS
    # =====================================================
    dept_stats = {
        "total_departments": WorkforcesDepartment.objects.count(),
        "users_assigned": User.objects.filter(department__isnull=False).count(),
    }
    
    return render(
        request,
        "admin/page/workstate_overview.html",
        {
            "workcycle_stats": workcycle_stats,
            "work_item_stats": work_item_stats,
            "review_stats": review_stats,
            "user_stats": user_stats,
            "file_stats": file_stats,
            "recent_submissions": recent_submissions,
            "pending_reviews": pending_reviews,
            "upcoming_deadlines": upcoming_deadlines,
            "dept_stats": dept_stats,
            "now": now,
        },
    )
