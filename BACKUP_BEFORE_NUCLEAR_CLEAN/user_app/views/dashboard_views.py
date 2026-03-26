"""
User Dashboard Views
Provides personalized analytics and overview for users.
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from accounts.models import WorkItem, WorkItemAttachment, UserAnalytics, DocumentFolder
from document_tracking.models import Submission


@login_required
def main_dashboard(request):
    """
    Main user dashboard - central hub for all modules.
    """
    user = request.user
    
    # Document Tracking Stats
    user_submissions = Submission.objects.filter(submitted_by=user)
    doc_tracking_stats = {
        'total_submissions': user_submissions.count(),
        'pending': user_submissions.filter(status__in=['pending_tracking', 'for_routing']).count(),
        'under_review': user_submissions.filter(status='under_review').count(),
        'approved': user_submissions.filter(status='approved').count(),
    }
    
    # Workstate Stats
    active_work_items = WorkItem.objects.filter(owner=user, is_active=True, workcycle__is_active=True)
    workstate_stats = {
        'total_work_items': active_work_items.count(),
        'not_started': active_work_items.filter(status='not_started').count(),
        'working_on_it': active_work_items.filter(status='working_on_it').count(),
        'done': active_work_items.filter(status='done').count(),
    }
    
    # File Manager Stats (user's uploaded files)
    user_files = WorkItemAttachment.objects.filter(uploaded_by=user)
    file_manager_stats = {
        'total_files': user_files.filter(file__isnull=False).count(),
        'total_links': user_files.filter(link_url__isnull=False).count(),
        'accepted': user_files.filter(acceptance_status='accepted').count(),
        'pending': user_files.filter(acceptance_status='pending').count(),
    }
    
    return render(request, 'user/page/main_dashboard.html', {
        'doc_tracking_stats': doc_tracking_stats,
        'workstate_stats': workstate_stats,
        'file_manager_stats': file_manager_stats,
    })


@login_required
def workstate_overview(request):
    """
    User workstate overview (renamed from dashboard).
    """
    user = request.user
    now = timezone.now()
    
    # =====================================================
    # GET OR CREATE USER ANALYTICS
    # =====================================================
    analytics = UserAnalytics.get_or_create_for_user(user)
    
    # =====================================================
    # ACTIVE WORK ITEMS
    # =====================================================
    active_work_items = (
        WorkItem.objects
        .filter(owner=user, is_active=True, workcycle__is_active=True)
        .select_related("workcycle")
        .order_by("workcycle__due_at")
    )
    
    work_item_stats = {
        "total": active_work_items.count(),
        "not_started": active_work_items.filter(status="not_started").count(),
        "working_on_it": active_work_items.filter(status="working_on_it").count(),
        "done": active_work_items.filter(status="done").count(),
    }
    
    # Review status counts (same logic as work-items page)
    review_stats = {
        "pending": active_work_items.filter(review_decision="pending").count(),
        "approved": active_work_items.filter(review_decision="approved").count(),
        "revision": active_work_items.filter(review_decision="revision").count(),
    }
    
    # =====================================================
    # LIFECYCLE STATE COUNTS (same logic as work-items page)
    # =====================================================
    soon_threshold = now + timedelta(days=3)
    
    lifecycle_counts = {
        "ongoing": active_work_items.filter(workcycle__due_at__gt=soon_threshold).count(),
        "due_soon": active_work_items.filter(
            workcycle__due_at__gt=now,
            workcycle__due_at__lte=soon_threshold
        ).count(),
        "lapsed": active_work_items.filter(workcycle__due_at__lte=now).count(),
    }
    
    # =====================================================
    # UPCOMING DEADLINES
    # =====================================================
    upcoming_deadlines = (
        active_work_items
        .filter(workcycle__due_at__gte=now, status__in=["not_started", "working_on_it"])
        .order_by("workcycle__due_at")[:5]
    )
    
    # =====================================================
    # ITEMS NEEDING ATTENTION
    # =====================================================
    needs_attention = []
    
    # Items needing revision
    revision_items = active_work_items.filter(review_decision="revision")
    for item in revision_items:
        needs_attention.append({
            "item": item,
            "reason": "Needs Revision",
            "priority": "high",
        })
    
    # Items not started with deadline approaching
    for item in active_work_items.filter(status="not_started"):
        if item.workcycle.lifecycle_state in ["due_soon", "lapsed"]:
            needs_attention.append({
                "item": item,
                "reason": "Not Started - Deadline Approaching",
                "priority": "high" if item.workcycle.lifecycle_state == "lapsed" else "medium",
            })
    
    # =====================================================
    # FILE STATS (from UserAnalytics model)
    # =====================================================
    file_stats = {
        "total": analytics.total_files_uploaded,
        "pending": analytics.total_files_uploaded - analytics.accepted_files - analytics.rejected_files,
        "accepted": analytics.accepted_files,
        "rejected": analytics.rejected_files,
    }
    
    # Recent file reviews (still query database for recent items)
    user_files = WorkItemAttachment.objects.filter(uploaded_by=user)
    recent_file_reviews = (
        user_files
        .exclude(acceptance_status="pending")
        .select_related("work_item__workcycle")
        .order_by("-accepted_at", "-rejected_at")[:5]
    )
    
    # =====================================================
    # PERFORMANCE METRICS
    # =====================================================
    performance = {
        "on_time_ratio": analytics.on_time_ratio,
        "approval_ratio": analytics.approval_ratio,
        "file_acceptance_ratio": analytics.file_acceptance_ratio,
        "total_completed": analytics.completed_work_items,
        "total_approved": analytics.approved_work_items,
    }
    
    # =====================================================
    # RECENT ACTIVITY (Recent work item updates)
    # =====================================================
    recent_activity = []
    
    # Recently completed items
    recently_completed = (
        active_work_items
        .filter(status="done", submitted_at__isnull=False)
        .order_by("-submitted_at")[:3]
    )
    for item in recently_completed:
        recent_activity.append({
            "item": item,
            "action": "Completed",
            "icon": "check-circle",
            "color": "green",
            "time": item.submitted_at,
        })
    
    # Recently started items (using created_at as proxy for when work started)
    recently_started = (
        active_work_items
        .filter(status="working_on_it")
        .exclude(id__in=[i.id for i in recently_completed])
        .order_by("-created_at")[:2]
    )
    for item in recently_started:
        recent_activity.append({
            "item": item,
            "action": "Working On",
            "icon": "spinner",
            "color": "orange",
            "time": item.created_at,
        })
    
    # Recently approved items
    recently_approved = (
        active_work_items
        .filter(review_decision="approved", reviewed_at__isnull=False)
        .order_by("-reviewed_at")[:2]
    )
    for item in recently_approved:
        recent_activity.append({
            "item": item,
            "action": "Approved",
            "icon": "check-double",
            "color": "teal",
            "time": item.reviewed_at,
        })
    
    # Sort by time (most recent first)
    recent_activity.sort(key=lambda x: x["time"] if x["time"] else timezone.now(), reverse=True)
    recent_activity = recent_activity[:5]
    
    return render(
        request,
        "user/page/workstate_overview.html",
        {
            "work_item_stats": work_item_stats,
            "review_stats": review_stats,
            "lifecycle_counts": lifecycle_counts,
            "upcoming_deadlines": upcoming_deadlines,
            "needs_attention": needs_attention[:5],
            "file_stats": file_stats,
            "recent_file_reviews": recent_file_reviews,
            "recent_activity": recent_activity,
            "performance": performance,
            "analytics": analytics,
            "now": now,
        },
    )


# Keep old dashboard function as alias for backwards compatibility
dashboard = workstate_overview
