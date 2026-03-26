from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from accounts.models import WorkItem, WorkItemMessage


# ============================================================
# REVIEW WORK ITEM (ADMIN)
# ============================================================
@xframe_options_exempt
@login_required
def review_work_item(request, item_id):
    """
    Admin review page for a submitted WorkItem.

    Responsibilities:
    - Display submission details
    - Group attachments by type
    - Update review_decision
    - Post persistent system message
    - 🔔 Fire REVIEW notification (service layer)
    """

    work_item = get_object_or_404(
        WorkItem.objects
        .select_related("owner", "workcycle")
        .prefetch_related("attachments", "messages"),
        id=item_id,
        status="done",
    )

    # --------------------------------------------------------
    # HANDLE REVIEW UPDATE
    # --------------------------------------------------------
    if request.method == "POST" and request.POST.get("action") == "update_review":
        decision = request.POST.get("review_decision")

        if decision not in {"pending", "approved", "revision"}:
            messages.error(request, "Invalid review decision submitted.")
            return redirect(
                "admin_app:work-item-review",
                item_id=work_item.id,
            )

        old_decision = work_item.review_decision

        if old_decision != decision:
            work_item.review_decision = decision
            work_item.save()  # reviewed_at handled in model.save()

            decision_label = decision.replace("_", " ").title()

            # --------------------------------------------
            # SYSTEM MESSAGE (AUDIT / DISCUSSION)
            # --------------------------------------------
            WorkItemMessage.objects.create(
                work_item=work_item,
                sender=request.user,
                sender_role=request.user.login_role,
                message=(
                    f"📝 Review Update\n\n"
                    f"This work item has been marked as {decision_label}."
                ),
            )

            # --------------------------------------------
            # CREATE ASYNC JOB FOR NOTIFICATIONS
            # --------------------------------------------
            from accounts.models import WorkItemReviewJob
            
            # Calculate file statistics for detailed notifications
            attachments = work_item.attachments.all()
            file_stats = {
                "total_files": attachments.count(),
                "accepted_files": attachments.filter(acceptance_status="accepted").count(),
                "rejected_files": attachments.filter(acceptance_status="rejected").count(),
                "pending_files": attachments.filter(acceptance_status="pending").count(),
            }
            
            WorkItemReviewJob.objects.create(
                work_item=work_item,
                old_decision=old_decision,
                new_decision=decision,
                reviewed_by=request.user,
                file_stats=file_stats,
            )

            messages.success(
                request,
                f"Review decision updated to {decision_label}."
            )
        else:
            messages.info(request, "Review decision was not changed.")

        return redirect(
            "admin_app:work-item-review",
            item_id=work_item.id,
        )

    # --------------------------------------------------------
    # GROUP ATTACHMENTS BY TYPE
    # --------------------------------------------------------
    attachments_by_type = defaultdict(list)
    for attachment in work_item.attachments.all():
        attachments_by_type[
            attachment.get_attachment_type_display()
        ].append(attachment)

    return render(
        request,
        "admin/page/review_work_item.html",
        {
            "work_item": work_item,
            "attachments_by_type": dict(attachments_by_type),
        },
    )


