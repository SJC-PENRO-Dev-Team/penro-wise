"""
API Views for Real-time Filtering
Provides JSON endpoints for AJAX-based filtering, searching, and sorting.
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F
from django.utils import timezone
from django.template.loader import render_to_string

from accounts.models import User, WorkCycle, WorkItem


# ============================================================
# WORKCYCLES API
# ============================================================
@login_required
def api_workcycles(request):
    """
    Real-time filtering API for workcycles page.
    Returns HTML partial for the workcycle cards.
    """
    state = request.GET.get("state", "").strip()
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()

    # Base queryset (active only)
    qs = (
        WorkCycle.objects
        .filter(is_active=True)
        .annotate(
            assignment_count=Count("assignments__id", distinct=True)
        )
        .prefetch_related(
            "assignments__assigned_user",
            "assignments__assigned_department",
        )
    )

    # Sorting
    if sort == "due_asc":
        qs = qs.order_by("due_at")
    elif sort == "due_desc":
        qs = qs.order_by("-due_at")
    else:
        qs = qs.order_by("-created_at")

    # Materialize for property-based filtering
    workcycles = list(qs)

    # Lifecycle filter
    if state:
        workcycles = [wc for wc in workcycles if wc.lifecycle_state == state]

    # Search filter
    if search_query:
        q_lower = search_query.lower()
        workcycles = [wc for wc in workcycles if q_lower in wc.title.lower()]

    # Calculate stats from ALL active (before filtering)
    all_active = list(qs)
    lifecycle_counts = {"ongoing": 0, "due_soon": 0, "lapsed": 0}
    for wc in all_active:
        if wc.lifecycle_state in lifecycle_counts:
            lifecycle_counts[wc.lifecycle_state] += 1

    # Add UI helpers
    for wc in workcycles:
        wc.has_department_assignment = wc.assignments.filter(
            assigned_department__isnull=False
        ).exists()

    # Render partial HTML
    html = render_to_string(
        "admin/page/_workcycle_cards.html",
        {
            "workcycles": workcycles,
            "now": timezone.now(),
        },
        request=request,
    )

    return JsonResponse({
        "html": html,
        "count": len(workcycles),
        "active_count": len(all_active),
        "lifecycle_counts": lifecycle_counts,
    })


# ============================================================
# USERS API
# ============================================================
@login_required
def api_users(request):
    """
    Real-time filtering API for users page.
    Returns HTML partial for the user cards.
    """
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()
    department = request.GET.get("department", "").strip()

    # Base queryset
    users_qs = User.objects.select_related("department")

    # Department filter
    if department:
        users_qs = users_qs.filter(department_id=department)

    # Search
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(position_title__icontains=search_query)
        )

    # Sorting
    if sort == "name_asc":
        users_qs = users_qs.order_by("first_name", "last_name")
    elif sort == "name_desc":
        users_qs = users_qs.order_by("-first_name", "-last_name")
    elif sort == "date_desc":
        users_qs = users_qs.order_by("-date_joined")
    elif sort == "date_asc":
        users_qs = users_qs.order_by("date_joined")
    elif sort == "role_asc":
        users_qs = users_qs.order_by("login_role", "first_name")
    else:
        users_qs = users_qs.order_by("-date_joined")

    users_list = list(users_qs)

    # Render partial HTML
    html = render_to_string(
        "admin/page/partials/_user_list.html",
        {"users": users_list},
        request=request,
    )

    return JsonResponse({
        "html": html,
        "count": len(users_list),
    })


# ============================================================
# ANALYTICS API
# ============================================================
@login_required
def api_analytics(request):
    """
    Real-time filtering API for completed work analytics page.
    Returns HTML partial for the analytics table.
    """
    state = request.GET.get("state", "").strip()
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "").strip()

    # Base query
    base_qs = (
        WorkItem.objects
        .filter(workcycle__is_active=True)
        .filter(
            Q(is_active=True) |
            Q(is_active=False, inactive_by=F("owner"))
        )
    )

    if search_query:
        base_qs = base_qs.filter(workcycle__title__icontains=search_query)

    # Per-workcycle aggregation
    summary_qs = (
        base_qs
        .values("workcycle_id", "workcycle__title", "workcycle__due_at", "workcycle__is_active")
        .annotate(
            total_workers=Count("id"),
            done_count=Count("id", filter=Q(status="done")),
            not_finished_count=Count("id", filter=Q(status__in=["not_started", "working_on_it"])),
            approved_count=Count("id", filter=Q(review_decision="approved")),
            revision_count=Count("id", filter=Q(review_decision="revision")),
            pending_count=Count("id", filter=Q(review_decision="pending")),
        )
    )

    # Sorting
    if sort == "due_asc":
        summary_qs = summary_qs.order_by("workcycle__due_at")
    elif sort == "due_desc":
        summary_qs = summary_qs.order_by("-workcycle__due_at")
    else:
        summary_qs = summary_qs.order_by("-workcycle__due_at")

    summaries = list(summary_qs)

    # Calculate percentages and lifecycle state
    now = timezone.now()
    from datetime import timedelta

    lifecycle_counts = {"ongoing": 0, "due_soon": 0, "lapsed": 0}

    for s in summaries:
        total = s["total_workers"] or 1
        s["done_pct"] = round((s["done_count"] / total) * 100)
        s["not_finished_pct"] = round((s["not_finished_count"] / total) * 100)
        s["approval_pct"] = round((s["approved_count"] / total) * 100) if s["done_count"] else 0

        # Lifecycle state
        due_at = s["workcycle__due_at"]
        if not s["workcycle__is_active"]:
            s["lifecycle_state"] = "archived"
        elif now >= due_at:
            s["lifecycle_state"] = "lapsed"
        elif (due_at - now) <= timedelta(days=3):
            s["lifecycle_state"] = "due_soon"
        else:
            s["lifecycle_state"] = "ongoing"

        if s["lifecycle_state"] in lifecycle_counts:
            lifecycle_counts[s["lifecycle_state"]] += 1

    # Filter by lifecycle state
    if state:
        summaries = [s for s in summaries if s["lifecycle_state"] == state]

    # Totals
    totals = {
        "total_workcycles": len(summaries),
        "ongoing": lifecycle_counts["ongoing"],
        "due_soon": lifecycle_counts["due_soon"],
        "lapsed": lifecycle_counts["lapsed"],
    }

    # Render partial HTML
    html = render_to_string(
        "admin/page/_completed_work_cards.html",
        {"summary": summaries, "now": now},
        request=request,
    )

    return JsonResponse({
        "html": html,
        "count": len(summaries),
        "totals": totals,
        "lifecycle_counts": lifecycle_counts,
    })
