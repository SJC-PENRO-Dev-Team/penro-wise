from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Max, Q
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from accounts.models import (
    WorkItem,
    WorkItemReadState,
    WorkCycle,
    HiddenDiscussion,
    User,
)


@login_required
def admin_work_item_threads(request):
    """
    Admin inbox view for WorkItem conversations.

    Ordering rules:
    1. Threads with unread messages first
    2. Newest activity first within each group
    """

    # --------------------------------------------------
    # GET HIDDEN ITEMS FOR THIS ADMIN
    # --------------------------------------------------
    hidden_work_item_ids = HiddenDiscussion.get_hidden_work_item_ids(request.user)
    hidden_workcycle_ids = HiddenDiscussion.get_hidden_workcycle_ids(request.user)
    
    # Get user threads hidden by admin
    hidden_user_threads = list(
        HiddenDiscussion.objects
        .filter(
            hidden_by=request.user,
            hide_type="user_thread"
        )
        .values_list("hidden_user_id", "workcycle_id")
    )

    # --------------------------------------------------
    # BASE QUERYSET (ONLY THREADS WITH MESSAGES)
    # --------------------------------------------------
    work_items = list(
        WorkItem.objects
        .select_related("owner", "workcycle")
        .prefetch_related("messages", "read_states")
        .annotate(
            message_count=Count("messages", distinct=True),
            last_message_at=Max("messages__created_at"),
        )
        .filter(message_count__gt=0)
        .exclude(id__in=hidden_work_item_ids)
        .exclude(workcycle_id__in=hidden_workcycle_ids)
        .order_by("-last_message_at", "-submitted_at")
    )
    
    # Filter out user threads hidden by admin
    if hidden_user_threads:
        work_items = [
            item for item in work_items
            if (item.owner_id, item.workcycle_id) not in hidden_user_threads
        ]

    # --------------------------------------------------
    # ATTACH UNREAD COUNT (PER ADMIN)
    # --------------------------------------------------
    total_unread = 0
    for item in work_items:
        read_state = next(
            (
                rs for rs in item.read_states.all()
                if rs.user_id == request.user.id
            ),
            None,
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        item.unread_count = (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )
        
        # Get last message for preview
        last_msg = item.messages.order_by("-created_at").first()
        item.last_message = last_msg.message if last_msg else None
        
        total_unread += item.unread_count

    # --------------------------------------------------
    # FINAL INBOX SORT
    # --------------------------------------------------
    # unread first → newest first
    work_items.sort(
        key=lambda item: (
            item.unread_count == 0,   # False (unread) comes first
            -(item.last_message_at.timestamp() if item.last_message_at else 0),
        )
    )
    
    # Count hidden items
    hidden_count = (
        len(hidden_work_item_ids) + 
        len(hidden_workcycle_ids) + 
        len(hidden_user_threads)
    )

    return render(
        request,
        "admin/page/work_item_thread_list.html",
        {
            "work_items": work_items,
            "total_active_threads": len(work_items),
            "total_unread": total_unread,
            "hidden_count": hidden_count,
        }
    )


# ============================================================
# HIDE DISCUSSION (ADMIN) - Work Item Level
# ============================================================
@login_required
@require_POST
def admin_hide_work_item_discussion(request, item_id):
    """Hide a specific work item discussion for the admin."""
    work_item = get_object_or_404(WorkItem, id=item_id)
    
    if HiddenDiscussion.objects.filter(
        hidden_by=request.user,
        work_item=work_item,
        hide_type="work_item"
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "Discussion is already hidden."
        })
    
    HiddenDiscussion.objects.create(
        hidden_by=request.user,
        hide_type="work_item",
        work_item=work_item
    )
    
    return JsonResponse({
        "success": True,
        "message": "Discussion hidden successfully."
    })


# ============================================================
# HIDE WORKCYCLE DISCUSSIONS (ADMIN)
# ============================================================
@login_required
@require_POST
def admin_hide_workcycle_discussions(request, workcycle_id):
    """Hide all discussions for a workcycle."""
    workcycle = get_object_or_404(WorkCycle, id=workcycle_id)
    
    if HiddenDiscussion.objects.filter(
        hidden_by=request.user,
        workcycle=workcycle,
        hide_type="workcycle"
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "Workcycle discussions are already hidden."
        })
    
    HiddenDiscussion.objects.create(
        hidden_by=request.user,
        hide_type="workcycle",
        workcycle=workcycle
    )
    
    return JsonResponse({
        "success": True,
        "message": f"All discussions for '{workcycle.title}' hidden."
    })


# ============================================================
# HIDE USER THREAD (ADMIN)
# ============================================================
@login_required
@require_POST
def admin_hide_user_thread(request, workcycle_id, user_id):
    """Hide a specific user's thread in a workcycle."""
    workcycle = get_object_or_404(WorkCycle, id=workcycle_id)
    target_user = get_object_or_404(User, id=user_id)
    
    if HiddenDiscussion.objects.filter(
        hidden_by=request.user,
        workcycle=workcycle,
        hidden_user=target_user,
        hide_type="user_thread"
    ).exists():
        return JsonResponse({
            "success": False,
            "message": "User thread is already hidden."
        })
    
    HiddenDiscussion.objects.create(
        hidden_by=request.user,
        hide_type="user_thread",
        workcycle=workcycle,
        hidden_user=target_user
    )
    
    return JsonResponse({
        "success": True,
        "message": f"Thread for {target_user.get_full_name() or target_user.username} hidden."
    })


# ============================================================
# UNHIDE DISCUSSION (ADMIN)
# ============================================================
@login_required
@require_POST
def admin_unhide_discussion(request, hidden_id):
    """Unhide a discussion by its HiddenDiscussion ID."""
    hidden = get_object_or_404(
        HiddenDiscussion,
        id=hidden_id,
        hidden_by=request.user
    )
    
    hidden.delete()
    
    return JsonResponse({
        "success": True,
        "message": "Discussion restored successfully."
    })


# ============================================================
# HIDDEN DISCUSSIONS LIST (ADMIN)
# ============================================================
@login_required
def admin_hidden_discussions(request):
    """Show all hidden discussions for the admin."""
    hidden_records = (
        HiddenDiscussion.objects
        .filter(hidden_by=request.user)
        .select_related(
            "work_item",
            "work_item__owner",
            "work_item__workcycle",
            "workcycle",
            "hidden_user"
        )
        .order_by("-hidden_at")
    )
    
    results = []
    for record in hidden_records:
        item_data = {
            "id": record.id,
            "hide_type": record.hide_type,
            "hidden_at": record.hidden_at,
        }
        
        if record.hide_type == "work_item" and record.work_item:
            item_data["title"] = record.work_item.workcycle.title
            item_data["subtitle"] = f"Thread with {record.work_item.owner.get_full_name() or record.work_item.owner.username}"
            item_data["icon"] = "fa-comment"
        elif record.hide_type == "workcycle" and record.workcycle:
            item_data["title"] = record.workcycle.title
            item_data["subtitle"] = "All discussions in this workcycle"
            item_data["icon"] = "fa-layer-group"
        elif record.hide_type == "user_thread" and record.hidden_user and record.workcycle:
            item_data["title"] = record.workcycle.title
            item_data["subtitle"] = f"Thread with {record.hidden_user.get_full_name() or record.hidden_user.username}"
            item_data["icon"] = "fa-user"
        else:
            continue  # Skip invalid records
            
        results.append(item_data)
    
    return render(
        request,
        "admin/page/hidden_discussions.html",
        {
            "hidden_items": results,
            "total_hidden": len(results),
        }
    )
