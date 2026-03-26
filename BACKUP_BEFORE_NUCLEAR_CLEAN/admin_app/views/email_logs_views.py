"""
Email Logs Views for Admin

Provides views for admins to view all system-wide email activity.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from notifications.models import EmailLog


@login_required
def admin_email_logs(request):
    """View all email logs (admin only)."""
    if request.user.login_role != "admin":
        return render(request, "403.html", status=403)
    
    # Get filter parameters
    email_type = request.GET.get("type")
    status = request.GET.get("status")
    search = request.GET.get("search", "").strip()
    
    # Base queryset - all emails for admin
    qs = EmailLog.objects.select_related("sender", "recipient").all()
    
    # Apply filters
    if email_type:
        qs = qs.filter(email_type=email_type)
    
    if status:
        qs = qs.filter(status=status)
    
    if search:
        qs = qs.filter(
            Q(subject__icontains=search) |
            Q(recipient_email__icontains=search) |
            Q(sender_email__icontains=search) |
            Q(recipient__first_name__icontains=search) |
            Q(recipient__last_name__icontains=search) |
            Q(sender__first_name__icontains=search) |
            Q(sender__last_name__icontains=search)
        )
    
    # Order by newest first
    qs = qs.order_by("-created_at")
    
    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    # Get counts for stats
    total_count = EmailLog.objects.count()
    sent_count = EmailLog.objects.filter(status="sent").count()
    failed_count = EmailLog.objects.filter(status="failed").count()
    
    return render(
        request,
        "admin/page/email_logs.html",
        {
            "page_obj": page_obj,
            "email_type": email_type,
            "status": status,
            "search": search,
            "email_types": EmailLog.EmailType.choices,
            "statuses": EmailLog.Status.choices,
            "total_count": total_count,
            "sent_count": sent_count,
            "failed_count": failed_count,
        }
    )


@login_required
def admin_email_detail(request, email_id):
    """Get email detail for modal (admin only)."""
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Forbidden"}, status=403)
    
    email_log = get_object_or_404(EmailLog, id=email_id)
    
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
    })
