from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from notifications.models import Notification
from notifications.services.discussion_messages import send_all_pending_message_digests


@login_required
def admin_notifications(request):
    if request.user.login_role != "admin":
        return render(request, "403.html", status=403)

    # Optional filters
    category = request.GET.get("category")
    unread_only = request.GET.get("unread")

    qs = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related("work_item", "workcycle")
    )

    if category:
        qs = qs.filter(category=category)

    if unread_only:
        qs = qs.filter(is_read=False)

    # Admin-first ordering:
    # 1. Unread
    # 2. Priority
    # 3. Newest
    qs = qs.order_by(
        "is_read",
        "-priority",
        "-created_at",
    )

    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "admin/page/notifications.html",
        {
            "page_obj": page_obj,
            "category": category,
            "categories": Notification.Category.choices,
        }
    )


@login_required
@require_POST
def send_bulk_message_digests(request):
    """
    Admin endpoint to manually trigger bulk message digest emails.
    
    This triggers the APScheduler job to send digests in the background.
    The actual sending happens asynchronously to avoid HTTP timeouts.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Forbidden"}, status=403)
    
    # Instead of sending synchronously (which causes timeouts),
    # we'll trigger the management command in the background
    from django.core.management import call_command
    import threading
    
    def send_digests_async():
        """Run the command in a background thread"""
        try:
            call_command("send_message_digests")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send message digests: {str(e)}")
    
    # Start background thread
    thread = threading.Thread(target=send_digests_async)
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        "success": True,
        "message": "Message digests are being sent in the background. Check email logs in a few minutes.",
    })
