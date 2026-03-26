"""
File Review Views
Handles file acceptance/rejection workflow for admin review.
"""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import WorkItemAttachment, UserAnalytics


@login_required
@require_POST
def accept_file(request, attachment_id):
    """
    Mark a file as accepted.
    Accepted files are stored permanently.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Permission denied"}, status=403)

    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)

    # Update acceptance status
    attachment.acceptance_status = "accepted"
    attachment.accepted_at = timezone.now()
    attachment.rejected_at = None
    attachment.rejection_expires_at = None
    attachment.rejection_reason = ""
    attachment.reviewed_by = request.user
    attachment.save()

    # Update user analytics
    if attachment.uploaded_by:
        analytics = UserAnalytics.get_or_create_for_user(attachment.uploaded_by)
        analytics.recalculate()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": "File accepted successfully",
            "status": "accepted",
            "attachment_id": attachment.id,
        })

    messages.success(request, "File accepted successfully.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def reject_file(request, attachment_id):
    """
    Mark a file as rejected.
    Rejected files will be auto-deleted after 24 hours.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Permission denied"}, status=403)

    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)
    reason = request.POST.get("reason", "").strip()

    # Update rejection status
    now = timezone.now()
    attachment.acceptance_status = "rejected"
    attachment.rejected_at = now
    attachment.rejection_expires_at = now + timedelta(days=1)  # 24 hours
    attachment.rejection_reason = reason
    attachment.accepted_at = None
    attachment.reviewed_by = request.user
    attachment.save()

    # Update user analytics
    if attachment.uploaded_by:
        analytics = UserAnalytics.get_or_create_for_user(attachment.uploaded_by)
        analytics.recalculate()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": "File rejected. It will be deleted in 24 hours.",
            "status": "rejected",
            "attachment_id": attachment.id,
            "expires_at": attachment.rejection_expires_at.isoformat(),
        })

    messages.warning(request, "File rejected. It will be deleted in 24 hours.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def undo_file_review(request, attachment_id):
    """
    Undo file acceptance or rejection.
    Returns file to pending status.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Permission denied"}, status=403)

    attachment = get_object_or_404(WorkItemAttachment, id=attachment_id)

    # Reset to pending
    attachment.acceptance_status = "pending"
    attachment.accepted_at = None
    attachment.rejected_at = None
    attachment.rejection_expires_at = None
    attachment.rejection_reason = ""
    attachment.reviewed_by = None
    attachment.save()

    # Update user analytics
    if attachment.uploaded_by:
        analytics = UserAnalytics.get_or_create_for_user(attachment.uploaded_by)
        analytics.recalculate()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": "File review undone",
            "status": "pending",
            "attachment_id": attachment.id,
        })

    messages.info(request, "File review undone.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def bulk_accept_files(request):
    """
    Accept multiple files at once.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Permission denied"}, status=403)

    attachment_ids = request.POST.getlist("attachment_ids[]")
    if not attachment_ids:
        return JsonResponse({"error": "No files selected"}, status=400)

    now = timezone.now()
    affected_users = set()

    attachments = WorkItemAttachment.objects.filter(id__in=attachment_ids)
    for attachment in attachments:
        attachment.acceptance_status = "accepted"
        attachment.accepted_at = now
        attachment.rejected_at = None
        attachment.rejection_expires_at = None
        attachment.rejection_reason = ""
        attachment.reviewed_by = request.user
        attachment.save()

        if attachment.uploaded_by:
            affected_users.add(attachment.uploaded_by)

    # Update analytics for affected users
    for user in affected_users:
        analytics = UserAnalytics.get_or_create_for_user(user)
        analytics.recalculate()

    return JsonResponse({
        "success": True,
        "message": f"{len(attachment_ids)} files accepted",
        "count": len(attachment_ids),
    })


@login_required
@require_POST
def bulk_reject_files(request):
    """
    Reject multiple files at once.
    """
    if request.user.login_role != "admin":
        return JsonResponse({"error": "Permission denied"}, status=403)

    attachment_ids = request.POST.getlist("attachment_ids[]")
    reason = request.POST.get("reason", "").strip()

    if not attachment_ids:
        return JsonResponse({"error": "No files selected"}, status=400)

    now = timezone.now()
    expires_at = now + timedelta(days=1)
    affected_users = set()

    attachments = WorkItemAttachment.objects.filter(id__in=attachment_ids)
    for attachment in attachments:
        attachment.acceptance_status = "rejected"
        attachment.rejected_at = now
        attachment.rejection_expires_at = expires_at
        attachment.rejection_reason = reason
        attachment.accepted_at = None
        attachment.reviewed_by = request.user
        attachment.save()

        if attachment.uploaded_by:
            affected_users.add(attachment.uploaded_by)

    # Update analytics for affected users
    for user in affected_users:
        analytics = UserAnalytics.get_or_create_for_user(user)
        analytics.recalculate()

    return JsonResponse({
        "success": True,
        "message": f"{len(attachment_ids)} files rejected",
        "count": len(attachment_ids),
    })
