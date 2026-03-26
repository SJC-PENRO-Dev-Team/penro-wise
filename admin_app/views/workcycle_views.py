from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q, F
from django.db.models.deletion import ProtectedError
from accounts.models import (
    User,
    WorkforcesDepartment,
    WorkCycle,
    WorkAssignment,
    WorkItem,
)

from admin_app.services.workcycle_service import (
    create_workcycle_with_assignments,
)

from admin_app.services.workcycle_reassign_service import (
    reassign_workcycle as reassign_workcycle_service,
)
from notifications.services.system import notify_workcycle_edited
from notifications.services.system import (
    notify_workcycle_archive_toggled,
    
)
from notifications.services.system import notify_workcycle_deleted
# ============================================================
# WORK CYCLE LIST
# ============================================================

@login_required
def workcycle_list(request):
    """
    Admin list view for ACTIVE Work Cycles

    Features:
    - Lifecycle filtering (?state=ongoing|due_soon|lapsed)
    - Search by title (?q=)
    - Sort by due date (?sort=due_asc|due_desc)
    - Stats always based on ALL active work cycles
    """

    # =========================================================
    # REQUEST PARAMS
    # =========================================================
    state = request.GET.get("state")
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort")  # due_asc | due_desc

    # =========================================================
    # BASE QUERYSET (ACTIVE ONLY)
    # =========================================================
    qs = (
        WorkCycle.objects
        .filter(is_active=True)
        .annotate(
            assignment_count=Count("assignments__id", distinct=True)
        )
        .prefetch_related(
            "assignments__assigned_user",
        )
    )

    # =========================================================
    # SORTING (DB-SAFE)
    # =========================================================
    if sort == "due_asc":
        qs = qs.order_by("due_at")
    elif sort == "due_desc":
        qs = qs.order_by("-due_at")
    else:
        qs = qs.order_by("-created_at")  # default

    # Materialize queryset (needed for lifecycle_state property)
    workcycles = list(qs)

    # =========================================================
    # LIFECYCLE FILTER (PROPERTY-SAFE)
    # =========================================================
    if state:
        workcycles = [
            wc for wc in workcycles
            if wc.lifecycle_state == state
        ]

    # =========================================================
    # SEARCH (TITLE)
    # =========================================================
    if search_query:
        q_lower = search_query.lower()
        workcycles = [
            wc for wc in workcycles
            if q_lower in wc.title.lower()
        ]

    # =========================================================
    # STATS (ALWAYS FROM *ALL* ACTIVE)
    # =========================================================
    all_active = list(qs)

    lifecycle_counts = {
        "ongoing": 0,
        "due_soon": 0,
        "lapsed": 0,
    }

    for wc in all_active:
        if wc.lifecycle_state in lifecycle_counts:
            lifecycle_counts[wc.lifecycle_state] += 1

    # =========================================================
    # UI HELPERS (SAFE, NO ORM ABUSE)
    # =========================================================
    for wc in workcycles:
        wc.has_department_assignment = wc.assignments.filter(
            assigned_department__isnull=False
        ).exists()

    # =========================================================
    # RENDER
    # =========================================================
    return render(
        request,
        "admin/page/workcycles.html",
        {
            "workcycles": workcycles,
            "active_count": len(all_active),
            "lifecycle_counts": lifecycle_counts,
            "current_state": state,
            "search_query": search_query,
            "current_sort": sort,   # 👈 for active ASC/DESC buttons
            "users": User.objects.filter(is_active=True, login_role="user"),
            "departments": WorkforcesDepartment.objects.all(),
            "now": timezone.now(),
        },
    )

@login_required
def inactive_workcycle_list(request):
    """
    Admin list view for INACTIVE (ARCHIVED) Work Cycles

    Filtering via:
      ?year=
      ?month=
      ?q=
      ?sort=due_asc | due_desc

    Reset state:
      no filters applied → "Total Inactive"
    """

    # =========================================================
    # BASE QUERYSET (INACTIVE ONLY)
    # =========================================================
    qs = (
        WorkCycle.objects
        .filter(is_active=False)
        .annotate(
            assignment_count=Count("assignments__id", distinct=True)
        )
        .prefetch_related(
            "assignments__assigned_user",
        )
    )

    all_inactive = list(qs)        # for stats + filter options
    workcycles = list(all_inactive)

    # =========================================================
    # FILTER PARAMS
    # =========================================================
    year_filter = request.GET.get("year")
    month_filter = request.GET.get("month")
    search_query = request.GET.get("q", "").strip()
    sort_param = request.GET.get("sort")   # 👈 ADD THIS

    # =========================================================
    # APPLY FILTERS (IN MEMORY – MATCHES YOUR CURRENT DESIGN)
    # =========================================================
    if year_filter:
        try:
            year_filter = int(year_filter)
            workcycles = [
                wc for wc in workcycles
                if wc.due_at and wc.due_at.year == year_filter
            ]
        except ValueError:
            pass

    if month_filter:
        try:
            month_filter = int(month_filter)
            workcycles = [
                wc for wc in workcycles
                if wc.due_at and wc.due_at.month == month_filter
            ]
        except ValueError:
            pass

    if search_query:
        q = search_query.lower()
        workcycles = [
            wc for wc in workcycles
            if q in wc.title.lower()
        ]

    # =========================================================
    # APPLY SORTING (FIXED)
    # =========================================================
    if sort_param == "due_asc":
        workcycles.sort(
            key=lambda wc: wc.due_at or timezone.datetime.max
        )

    elif sort_param == "due_desc":
        workcycles.sort(
            key=lambda wc: wc.due_at or timezone.datetime.min,
            reverse=True
        )

    # =========================================================
    # STATS (ALWAYS BASED ON *ALL* INACTIVE)
    # =========================================================
    inactive_count = len(all_inactive)

    # =========================================================
    # UI STATE
    # =========================================================
    has_filters = any([
        year_filter,
        month_filter,
        search_query,
        sort_param,
    ])

    # =========================================================
    # FILTER OPTIONS (BASED ON ALL INACTIVE)
    # =========================================================
    years = sorted({
        wc.due_at.year
        for wc in all_inactive
        if wc.due_at
    })

    months = [
        {"value": 1, "label": "January"},
        {"value": 2, "label": "February"},
        {"value": 3, "label": "March"},
        {"value": 4, "label": "April"},
        {"value": 5, "label": "May"},
        {"value": 6, "label": "June"},
        {"value": 7, "label": "July"},
        {"value": 8, "label": "August"},
        {"value": 9, "label": "September"},
        {"value": 10, "label": "October"},
        {"value": 11, "label": "November"},
        {"value": 12, "label": "December"},
    ]

    # =========================================================
    # RENDER
    # =========================================================
    return render(
        request,
        "admin/page/workcycles-inactive.html",
        {
            "workcycles": workcycles,
            "inactive_count": inactive_count,
            "years": years,
            "months": months,
            "search_query": search_query,
            "has_filters": has_filters,
            "now": timezone.now(),
            "users": User.objects.filter(is_active=True, login_role="user"),
            "departments": WorkforcesDepartment.objects.all(),
        },
    )

# ============================================================
# CREATE WORK CYCLE
# ============================================================
@login_required
def create_workcycle(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description", "")

        # -----------------------------
        # DUE DATE (TIMEZONE-SAFE)
        # -----------------------------
        due_at_raw = request.POST.get("due_at")
        due_at = parse_datetime(due_at_raw)

        if not due_at:
            messages.error(request, "Invalid due date.")
            return redirect("admin_app:workcycles")

        if timezone.is_naive(due_at):
            due_at = timezone.make_aware(
                due_at,
                timezone.get_current_timezone()
            )

        # -----------------------------
        # USERS (OPTIONAL)
        # -----------------------------
        raw_user_ids = request.POST.getlist("users[]")
        user_ids = [uid for uid in raw_user_ids if uid.isdigit()]
        users = User.objects.filter(id__in=user_ids)

        # -----------------------------
        # DEPARTMENT (OPTIONAL)
        # -----------------------------
        department_id = request.POST.get("department")
        department = WorkforcesDepartment.objects.filter(id=department_id).first() if department_id else None

        # -----------------------------
        # SAFETY CHECK
        # -----------------------------
        if not users.exists() and not department:
            messages.error(
                request,
                "You must assign at least one user or a department."
            )
            return redirect("admin_app:workcycles")

        # -----------------------------
        # CREATE WORK CYCLE (FAST)
        # -----------------------------
        workcycle = create_workcycle_with_assignments(
            title=title,
            description=description,
            due_at=due_at,  # ✅ timezone-aware
            created_by=request.user,
            users=users,
            department=department,
        )

        # -----------------------------
        # CREATE EMAIL JOB (ASYNC)
        # -----------------------------
        from accounts.models import WorkCycleEmailJob
        
        WorkCycleEmailJob.objects.create(
            workcycle=workcycle,
            job_type="created",
            actor=request.user,
        )

        messages.success(
            request,
            f"Work cycle '{workcycle.title}' created successfully. "
            f"Work items and email notifications are being processed in the background."
        )
        return redirect("admin_app:workcycles")

    # -----------------------------
    # GET REQUEST
    # -----------------------------
    return render(
        request,
        "admin/page/workcycle_create.html",
        {
            "users": User.objects.filter(is_active=True, login_role="user"),
            "departments": WorkforcesDepartment.objects.all(),
        },
    )

# ============================================================
# EDIT WORK CYCLE
# ============================================================
@login_required
def edit_workcycle(request):
    if request.method == "POST":
        wc_id = request.POST.get("workcycle_id")
        workcycle = get_object_or_404(WorkCycle, id=wc_id)

        # 🔥 capture old state BEFORE edit
        old_due_at = workcycle.due_at

        workcycle.title = request.POST.get("title")
        workcycle.description = request.POST.get("description", "")

        due_at_raw = request.POST.get("due_at")
        due_at = parse_datetime(due_at_raw)

        if not due_at:
            messages.error(request, "Invalid due date.")
            return redirect("admin_app:workcycles")

        if timezone.is_naive(due_at):
            due_at = timezone.make_aware(
                due_at,
                timezone.get_current_timezone()
            )

        workcycle.due_at = due_at
        workcycle.save(update_fields=["title", "description", "due_at"])

        # ✅ CREATE EMAIL JOB (ASYNC) - Only if due date changed
        from accounts.models import WorkCycleEmailJob
        
        if old_due_at != workcycle.due_at:
            WorkCycleEmailJob.objects.create(
                workcycle=workcycle,
                job_type="edited",
                actor=request.user,
                old_due_at=old_due_at,
            )

        # ✅ SYSTEM IN-APP NOTIFICATION (IMMEDIATE)
        notify_workcycle_edited(
            workcycle=workcycle,
            edited_by=request.user,
            old_due_at=old_due_at,
        )

        messages.success(
            request, 
            "Work cycle updated successfully. Email notifications are being sent in the background."
        )
        return redirect("admin_app:workcycles")

# ============================================================
# REASSIGN WORK CYCLE
# ============================================================
@login_required
def reassign_workcycle(request):
    if request.method != "POST":
        return redirect("admin_app:workcycles")

    if request.user.login_role != "admin":
        messages.error(request, "You are not allowed to perform this action.")
        return redirect("admin_app:workcycles")

    wc_id = request.POST.get("workcycle_id")
    workcycle = get_object_or_404(WorkCycle, id=wc_id)

    # USERS
    raw_user_ids = request.POST.getlist("users[]")
    user_ids = [uid for uid in raw_user_ids if uid.isdigit()]
    users = User.objects.filter(id__in=user_ids)

    # DEPARTMENT
    department_id = request.POST.get("department")
    department = WorkforcesDepartment.objects.filter(id=department_id).first() if department_id else None

    # NOTE
    inactive_note = request.POST.get("inactive_note", "").strip()

    if not users.exists() and not department:
        messages.error(
            request,
            "You must assign at least one user or a department."
        )
        return redirect("admin_app:workcycles")

    reassign_workcycle_service(
        workcycle=workcycle,
        users=users,
        department=department,
        inactive_note=inactive_note,
        performed_by=request.user,  # ✅ correct
    )

    # ✅ CREATE EMAIL JOB (ASYNC)
    from accounts.models import WorkCycleEmailJob
    
    WorkCycleEmailJob.objects.create(
        workcycle=workcycle,
        job_type="reassigned",
        actor=request.user,
        inactive_note=inactive_note,
    )

    messages.success(
        request, 
        "Work cycle reassigned successfully. Email notifications are being sent in the background."
    )
    return redirect("admin_app:workcycles")


# ============================================================
# WORK CYCLE HISTORY (READ-ONLY AUDIT VIEW)
# ============================================================

@login_required
def workcycle_history(request, pk):
    """
    Read-only history page for archived/inactive workcycles.
    Shows all assigned users, their statuses, file reviews, and audit details.
    """
    from accounts.models import WorkItemAttachment, WorkItemMessage
    
    if request.user.login_role != "admin":
        return render(request, "403.html", status=403)
    
    workcycle = get_object_or_404(
        WorkCycle.objects.select_related("created_by"),
        pk=pk
    )
    
    # Get all work items for this workcycle
    work_items = (
        WorkItem.objects
        .filter(workcycle=workcycle)
        .select_related("owner", "inactive_by")
        .prefetch_related("attachments", "messages")
        .order_by("owner__last_name", "owner__first_name")
    )
    
    # Build detailed history data for each user
    user_histories = []
    
    # Aggregate stats
    total_users = work_items.count()
    total_submitted = 0
    total_approved = 0
    total_revision = 0
    total_files = 0
    total_accepted = 0
    total_rejected = 0
    
    for item in work_items:
        # Get attachments for this work item
        attachments = item.attachments.all().select_related("reviewed_by", "uploaded_by")
        
        # Get messages count
        messages_count = item.messages.count()
        
        # Calculate submission timing
        submission_status = None
        submission_delta = None
        if item.submitted_at and workcycle.due_at:
            delta = workcycle.due_at - item.submitted_at
            if delta.total_seconds() >= 0:
                submission_status = "on_time"
            else:
                late = abs(delta)
                days = late.days
                hours = late.seconds // 3600
                submission_delta = f"{days}d {hours}h" if days > 0 else f"{hours}h"
                submission_status = "late"
        
        # File stats for this user
        user_files = attachments.count()
        user_accepted = attachments.filter(acceptance_status="accepted").count()
        user_rejected = attachments.filter(acceptance_status="rejected").count()
        user_pending = attachments.filter(acceptance_status="pending").count()
        
        # Update aggregates
        if item.status == "done":
            total_submitted += 1
        if item.review_decision == "approved":
            total_approved += 1
        elif item.review_decision == "revision":
            total_revision += 1
        total_files += user_files
        total_accepted += user_accepted
        total_rejected += user_rejected
        
        user_histories.append({
            "work_item": item,
            "user": item.owner,
            "status": item.status,
            "review_decision": item.review_decision,
            "submitted_at": item.submitted_at,
            "reviewed_at": item.reviewed_at,
            "submission_status": submission_status,
            "submission_delta": submission_delta,
            "is_active": item.is_active,
            "inactive_reason": item.inactive_reason,
            "inactive_note": item.inactive_note,
            "inactive_at": item.inactive_at,
            "inactive_by": item.inactive_by,
            "attachments": attachments,
            "files_total": user_files,
            "files_accepted": user_accepted,
            "files_rejected": user_rejected,
            "files_pending": user_pending,
            "messages_count": messages_count,
        })
    
    # Summary stats
    summary = {
        "total_users": total_users,
        "total_submitted": total_submitted,
        "total_not_submitted": total_users - total_submitted,
        "total_approved": total_approved,
        "total_revision": total_revision,
        "total_pending": total_users - total_approved - total_revision,
        "total_files": total_files,
        "total_accepted": total_accepted,
        "total_rejected": total_rejected,
        "total_pending_files": total_files - total_accepted - total_rejected,
        "completion_rate": round((total_submitted / total_users * 100) if total_users > 0 else 0, 1),
        "approval_rate": round((total_approved / total_submitted * 100) if total_submitted > 0 else 0, 1),
    }
    
    return render(
        request,
        "admin/page/workcycle_history.html",
        {
            "workcycle": workcycle,
            "user_histories": user_histories,
            "summary": summary,
        }
    )


# ============================================================
# WORK CYCLE ASSIGNMENT DETAILS
# ============================================================

def workcycle_assignments(request, pk):
    # =====================================================
    # LOAD WORK CYCLE
    # =====================================================
    workcycle = get_object_or_404(WorkCycle, pk=pk)

    # =====================================================
    # ASSIGNMENTS
    # =====================================================
    assignments = (
        WorkAssignment.objects
        .filter(workcycle=workcycle)
        .select_related("assigned_user", "assigned_department")
    )

    # =====================================================
    # ACTIVE LIST
    # (active = True) OR (inactive AND archived by owner)
    # =====================================================
    active_items = (
        WorkItem.objects
        .filter(workcycle=workcycle)
        .filter(
            Q(is_active=True)
            |
            Q(
                is_active=False,
                inactive_by=F("owner"),
            )
        )
        .select_related("owner", "workcycle")
    )

    # =====================================================
    # ARCHIVED LIST
    # (inactive AND NOT archived by owner)
    # =====================================================
    archived_items = (
        WorkItem.objects
        .filter(
            workcycle=workcycle,
            is_active=False,
        )
        .exclude(
            inactive_by=F("owner")
        )
        .select_related("owner", "workcycle")
    )

    # ----------------------------------
    # SUBMISSION STATUS CALCULATION
    # ----------------------------------
    for item in list(active_items) + list(archived_items):
        if item.submitted_at:
            delta = item.workcycle.due_at - item.submitted_at

            if delta.total_seconds() >= 0:
                item.submission_status = "on_time"
                item.submission_delta = None
            else:
                late = abs(delta)
                days = late.days
                hours = late.seconds // 3600

                item.submission_delta = (
                    f"{days}d {hours}h" if days > 0 else f"{hours}h"
                )
                item.submission_status = "late"
        else:
            item.submission_status = None
            item.submission_delta = None

    # =====================================================
    # COUNTS (ACTIVE SEMANTICS)
    # =====================================================
    status_counts = {
        "done": active_items.filter(status="done").count(),
        "working_on_it": active_items.filter(status="working_on_it").count(),
        "not_started": active_items.filter(status="not_started").count(),
    }

    review_counts = {
        "pending": active_items.filter(review_decision="pending").count(),
        "approved": active_items.filter(review_decision="approved").count(),
        "revision": active_items.filter(review_decision="revision").count(),
    }

    return render(
        request,
        "admin/page/workcycle_assignments.html",
        {
            "workcycle": workcycle,
            "assignments": assignments,

            # UI buckets
            "active_items": active_items,
            "archived_items": archived_items,

            # Stats
            "status_counts": status_counts,
            "review_counts": review_counts,
        },
    )
# ============================================================
# TOGGLE WORK CYCLE ARCHIVE
# ============================================================

@require_POST
def toggle_workcycle_archive(request, pk):
    """
    Toggle WorkCycle active / archived state.

    - Active → Archived
    - Archived → Restored

    Reminder system automatically respects is_active flag.
    """

    workcycle = get_object_or_404(WorkCycle, pk=pk)

    workcycle.is_active = not workcycle.is_active
    workcycle.save(update_fields=["is_active"])

    # ✅ SYSTEM IN-APP NOTIFICATION
    notify_workcycle_archive_toggled(
        workcycle=workcycle,
        actor=request.user,
    )

    if workcycle.is_active:
        messages.success(
            request,
            "Work cycle restored successfully."
        )
    else:
        messages.success(
            request,
            "Work cycle archived successfully."
        )

    return redirect("admin_app:workcycles")


# ============================================================
# DELETE WORK CYCLE (HARD DELETE)
# ============================================================

@require_POST
def delete_workcycle(request, pk):
    """
    Permanently delete a WorkCycle.

    - If protected by related objects (folders, documents),
      deletion is blocked and user is instructed to archive instead.
    - Force delete option allows deleting parent while preserving children.
    """
    from django.http import JsonResponse
    
    workcycle = get_object_or_404(WorkCycle, pk=pk)
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    redirect_to = request.META.get(
        "HTTP_REFERER",
        reverse("admin_app:workcycles")
    )

    # Check for force delete
    force_delete = request.POST.get('force_delete') == 'true'
    confirmation_phrase = request.POST.get('confirmation_phrase', '').strip()
    
    try:
        title = workcycle.title

        # 🔥 capture affected users BEFORE delete
        affected_user_ids = list(
            workcycle.work_items
            .values_list("owner_id", flat=True)
            .distinct()
        )

        workcycle.delete()

        # ✅ SYSTEM IN-APP NOTIFICATION
        if affected_user_ids:
            notify_workcycle_deleted(
                workcycle_title=title,
                actor=request.user,
                affected_user_ids=affected_user_ids,
            )

        if is_ajax:
            return JsonResponse({
                'status': 'success',
                'message': f"Work cycle '{title}' was permanently deleted."
            })
        
        messages.success(
            request,
            f"Work cycle '{title}' was permanently deleted."
        )

    except ProtectedError as e:
        # Check if force delete was requested with correct confirmation
        if force_delete:
            expected_phrase = f"DELETE {workcycle.title}"
            if confirmation_phrase.upper() == expected_phrase.upper():
                # Force delete: nullify foreign keys on related objects
                title = workcycle.title
                
                # Nullify workcycle reference on folders
                from structure.models import DocumentFolder
                DocumentFolder.objects.filter(workcycle=workcycle).update(workcycle=None)
                
                # Now delete the workcycle
                workcycle.delete()
                
                # ✅ SYSTEM IN-APP NOTIFICATION
                if affected_user_ids:
                    notify_workcycle_deleted(
                        workcycle_title=title,
                        actor=request.user,
                        affected_user_ids=affected_user_ids,
                    )
                
                if is_ajax:
                    return JsonResponse({
                        'status': 'success',
                        'message': f"Work cycle '{title}' was force deleted. Related documents preserved."
                    })
                
                messages.success(
                    request,
                    f"Work cycle '{title}' was force deleted. Related documents preserved."
                )
                return redirect(redirect_to)
            else:
                if is_ajax:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Confirmation phrase does not match. Please try again.'
                    })
                messages.error(request, 'Confirmation phrase does not match. Please try again.')
                return redirect(redirect_to)
        
        # Get count of protected objects for better error message
        protected_count = 0
        try:
            from structure.models import DocumentFolder
            protected_count = DocumentFolder.objects.filter(workcycle=workcycle).count()
        except:
            pass
        
        error_msg = (
            f"This work cycle cannot be deleted because it has "
            f"{protected_count} linked document(s)/folder(s). "
            f"Use force delete or archive it instead."
        )
        
        if is_ajax:
            return JsonResponse({
                'status': 'protected',
                'message': error_msg,
                'workcycle_id': pk,
                'workcycle_title': workcycle.title,
                'protected_count': protected_count
            })
        
        messages.error(request, error_msg)

    return redirect(redirect_to)