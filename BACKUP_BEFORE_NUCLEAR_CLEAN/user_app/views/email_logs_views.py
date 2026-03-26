"""
Email Logs Views for Users

Provides views for users to view their own email activity (sent and received).
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from notifications.models import EmailLog


@login_required
def user_email_logs(request):
    """View user's own email logs."""
    if request.user.login_role != "user":
        return render(request, "403.html", status=403)
    
    # Get filter parameters
    email_type = request.GET.get("type")
    status = request.GET.get("status")
    direction = request.GET.get("direction")  # sent or received
    
    # Base queryset - only emails where user is sender or recipient
    qs = EmailLog.objects.select_related("sender", "recipient").filter(
        Q(sender=request.user) | Q(recipient=request.user)
    )
    
    # Apply filters
    if email_type:
        qs = qs.filter(email_type=email_type)
    
    if status:
        qs = qs.filter(status=status)
    
    if direction == "sent":
        qs = qs.filter(sender=request.user)
    elif direction == "received":
        qs = qs.filter(recipient=request.user)
    
    # Order by newest first
    qs = qs.order_by("-created_at")
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get counts for stats
    total_count = EmailLog.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).count()
    sent_count = EmailLog.objects.filter(sender=request.user).count()
    received_count = EmailLog.objects.filter(recipient=request.user).count()
    unread_count = EmailLog.objects.filter(
        recipient=request.user,
        is_read=False,
        status=EmailLog.Status.SENT
    ).count()
    
    return render(
        request,
        "user/page/email_logs.html",
        {
            "page_obj": page_obj,
            "email_type": email_type,
            "status": status,
            "direction": direction,
            "email_types": EmailLog.EmailType.choices,
            "statuses": EmailLog.Status.choices,
            "total_count": total_count,
            "sent_count": sent_count,
            "received_count": received_count,
            "unread_count": unread_count,
        }
    )


@login_required
def user_email_detail(request, email_id):
    """Get email detail for modal (user's own emails only)."""
    if request.user.login_role != "user":
        return JsonResponse({"error": "Forbidden"}, status=403)
    
    # Only allow viewing emails where user is sender or recipient
    email_log = get_object_or_404(
        EmailLog,
        Q(sender=request.user) | Q(recipient=request.user),
        id=email_id
    )
    
    # Mark as read if user is the recipient
    if email_log.recipient == request.user:
        email_log.mark_as_read()
    
    # Get sender/recipient names
    sender_name = None
    if email_log.sender:
        sender_name = email_log.sender.get_full_name() or email_log.sender.username
    
    recipient_name = None
    if email_log.recipient:
        recipient_name = email_log.recipient.get_full_name() or email_log.recipient.username
    
    return JsonResponse({
        "id": email_log.id,
        "subject": email_log.subject,
        "sender_email": email_log.sender_email,
        "sender_name": sender_name,
        "recipient_email": email_log.recipient_email,
        "recipient_name": recipient_name,
        "body_text": email_log.body_text,
        "body_html": email_log.body_html,
        "email_type": email_log.email_type,
        "email_type_display": email_log.get_email_type_display(),
        "status": email_log.status,
        "status_display": email_log.get_status_display(),
        "error_message": email_log.error_message,
        "created_at": email_log.created_at.strftime("%b %d, %Y at %I:%M %p"),
        "sent_at": email_log.sent_at.strftime("%b %d, %Y at %I:%M %p") if email_log.sent_at else None,
        "is_read": email_log.is_read,
        "read_at": email_log.read_at.strftime("%b %d, %Y at %I:%M %p") if email_log.read_at else None,
    })
