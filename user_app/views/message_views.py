# user_app/views/message_views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, Max
from django.http import JsonResponse
from datetime import timedelta

from accounts.models import (
    WorkItem,
    WorkItemMessage,
    WorkItemReadState,
    WorkCycle,
    HiddenDiscussion,
)
from notifications.services.discussion_messages import notify_new_discussion_message



# ============================================================
# DISCUSSIONS LIST (USER)
# ============================================================
@login_required
def user_discussions_list(request):
    # Get hidden work item IDs for this user
    hidden_ids = HiddenDiscussion.get_hidden_work_item_ids(request.user)
    
    work_items = (
        WorkItem.objects
        .filter(owner=request.user, is_active=True)
        .exclude(id__in=hidden_ids)  # Exclude hidden discussions
        .select_related("workcycle", "workcycle__created_by")
        .prefetch_related("messages", "read_states")
    )

    results = []
    total_unread = 0

    for item in work_items:
        read_state = next(
            (rs for rs in item.read_states.all() if rs.user_id == request.user.id),
            None
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        unread_count = (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )

        total_unread += unread_count

        # Get last message for preview
        last_msg = item.messages.order_by("-created_at").first()

        results.append({
            "work_item": item,
            "unread_count": unread_count,
            "last_message_at": last_msg.created_at if last_msg else None,
            "last_message": last_msg.message if last_msg else None,
            "total_message_count": item.messages.count(),
        })

    # Sort by last message time (most recent first)
    from datetime import datetime, timezone as dt_timezone
    results.sort(
        key=lambda x: x["last_message_at"] or datetime.min.replace(tzinfo=dt_timezone.utc),
        reverse=True
    )

    return render(
        request,
        "user/page/discussions_list.html",
        {
            "work_items": results,
            "total_unread": total_unread,
            "hidden_count": len(hidden_ids),
        }
    )

# ============================================================
# WORK ITEM DISCUSSION (USER)
# ============================================================
@login_required
@xframe_options_exempt
def user_work_item_discussion(request, item_id):
    work_item = get_object_or_404(
        WorkItem.objects.select_related("owner", "workcycle"),
        id=item_id,
        owner=request.user,
    )

    # -----------------------------
    # POST MESSAGE
    # -----------------------------
    if request.method == "POST":
        text = request.POST.get("message", "").strip()

        if not text:
            messages.warning(request, "Message cannot be empty.")
            return redirect("user_app:work-item-discussion", item_id=work_item.id)

        new_message = WorkItemMessage.objects.create(
            work_item=work_item,
            sender=request.user,
            message=text,
        )
        
        # ✅ Create in-app notification for the recipient (admins)
        notify_new_discussion_message(new_message)

        return redirect("user_app:work-item-discussion", item_id=work_item.id)

    # -----------------------------
    # MARK THREAD AS READ
    # -----------------------------
    WorkItemMessage.mark_thread_as_read(
        work_item=work_item,
        reader=request.user
    )

    # -----------------------------
    # LOAD MESSAGES
    # -----------------------------
    messages_qs = (
        work_item.messages
        .select_related("sender")
        .order_by("created_at", "id")
    )

    # -----------------------------
    # GET OTHER PARTY'S READ STATE (for read receipts)
    # For user: check if admin has read their messages
    # -----------------------------
    other_read_state = (
        WorkItemReadState.objects
        .filter(work_item=work_item)
        .exclude(user=request.user)
        .order_by("-last_read_at")
        .first()
    )
    
    last_read_message_id = (
        other_read_state.last_read_message_id
        if other_read_state and other_read_state.last_read_message_id
        else 0
    )

    return render(
        request,
        "user/page/work_item_discussion.html",
        {
            "work_item": work_item,
            "messages": messages_qs,
            "has_messages": messages_qs.exists(),
            "last_read_message_id": last_read_message_id,
        }
    )

# ============================================================
# MARK ALL AS READ (BULK ACTION)
# ============================================================
@login_required
def user_mark_all_discussions_read(request):
    if request.method == "POST":
        now = timezone.now()

        for item in WorkItem.objects.filter(owner=request.user, is_active=True):
            last_msg = (
                item.messages
                .exclude(sender=request.user)
                .order_by("-id")
                .first()
            )

            if last_msg:
                WorkItemReadState.objects.update_or_create(
                    work_item=item,
                    user=request.user,
                    defaults={
                        "last_read_message": last_msg,
                        "last_read_at": now,
                    }
                )

        messages.success(request, "All discussions marked as read.")

    return redirect("user_app:discussions-list")

# ============================================================
# GET DISCUSSION STATS (API ENDPOINT)
# ============================================================
@login_required
def user_discussion_stats(request):
    total_unread = 0
    active_conversations = 0

    work_items = (
        WorkItem.objects
        .filter(owner=request.user, is_active=True)
        .prefetch_related("messages", "read_states")
    )

    recent_cutoff = timezone.now() - timedelta(days=7)

    for item in work_items:
        read_state = next(
            (rs for rs in item.read_states.all() if rs.user_id == request.user.id),
            None
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        unread = (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )

        total_unread += unread

        if item.messages.filter(created_at__gte=recent_cutoff).exists():
            active_conversations += 1

    conversations_by_status = {}
    for state in WorkCycle.LifecycleState:
        conversations_by_status[state.label] = sum(
            1 for item in work_items
            if item.workcycle.lifecycle_state == state.value
        )

    return JsonResponse({
        "total_conversations": work_items.count(),
        "total_unread": total_unread,
        "active_conversations": active_conversations,
        "conversations_by_status": conversations_by_status,
    })

# ============================================================
# UTILITY: Get Unread Count for Navigation Badge
# ============================================================
def get_user_total_unread_count(user):
    total = 0

    items = (
        WorkItem.objects
        .filter(owner=user, is_active=True)
        .prefetch_related("messages", "read_states")
    )

    for item in items:
        read_state = next(
            (rs for rs in item.read_states.all() if rs.user_id == user.id),
            None
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        total += (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=user)
            .count()
        )

    return total


# ============================================================
# HIDE DISCUSSION (USER)
# ============================================================
@login_required
@require_POST
def hide_discussion(request, item_id):
    """Hide a work item discussion for the current user."""
    work_item = get_object_or_404(
        WorkItem,
        id=item_id,
        owner=request.user,
        is_active=True
    )
    
    # Check if already hidden
    if HiddenDiscussion.is_hidden_for_user(request.user, work_item):
        return JsonResponse({
            "success": False,
            "message": "Discussion is already hidden."
        })
    
    # Create hidden record
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
# UNHIDE DISCUSSION (USER)
# ============================================================
@login_required
@require_POST
def unhide_discussion(request, item_id):
    """Unhide a work item discussion for the current user."""
    work_item = get_object_or_404(
        WorkItem,
        id=item_id,
        owner=request.user
    )
    
    # Delete hidden record
    deleted, _ = HiddenDiscussion.objects.filter(
        hidden_by=request.user,
        work_item=work_item,
        hide_type="work_item"
    ).delete()
    
    if deleted:
        return JsonResponse({
            "success": True,
            "message": "Discussion restored successfully."
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "Discussion was not hidden."
        })


# ============================================================
# HIDDEN DISCUSSIONS LIST (USER)
# ============================================================
@login_required
def hidden_discussions_list(request):
    """Show all hidden discussions for the current user."""
    hidden_records = (
        HiddenDiscussion.objects
        .filter(
            hidden_by=request.user,
            hide_type="work_item",
            work_item__isnull=False
        )
        .select_related(
            "work_item",
            "work_item__workcycle",
            "work_item__workcycle__created_by"
        )
        .order_by("-hidden_at")
    )
    
    results = []
    for record in hidden_records:
        item = record.work_item
        
        # Get last message for preview
        last_msg = item.messages.order_by("-created_at").first()
        
        results.append({
            "work_item": item,
            "hidden_at": record.hidden_at,
            "last_message_at": last_msg.created_at if last_msg else None,
            "last_message": last_msg.message if last_msg else None,
            "total_message_count": item.messages.count(),
        })
    
    return render(
        request,
        "user/page/hidden_discussions.html",
        {
            "hidden_items": results,
            "total_hidden": len(results),
        }
    )
