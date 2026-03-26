from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)
from accounts.models import WorkItem


# ============================================================
# WORK ITEM STATUS CHANGED (USER → ADMIN / CREATOR)
# ============================================================

def notify_work_item_status_changed(
    *,
    work_item: WorkItem,
    actor,
    old_status: str | None,
):
    """
    Notify the WorkCycle creator (admin) when a user
    changes the status of a work item.

    Supports:
    - submit (→ done)
    - undo submit (done → working_on_it)
    - normal status changes

    Channels:
    - In-app notification
    - Gmail SMTP email (with HTML)
    """

    # --------------------------------------------------
    # SAFETY GUARDS
    # --------------------------------------------------
    admin = work_item.workcycle.created_by
    if not admin:
        return

    if old_status == work_item.status:
        return

    valid_statuses = {"not_started", "working_on_it", "done"}
    if old_status not in valid_statuses or work_item.status not in valid_statuses:
        return

    actor_name = actor.get_full_name() or actor.username
    wc_title = work_item.workcycle.title

    # --------------------------------------------------
    # DETERMINE TRANSITION
    # --------------------------------------------------
    if old_status != "done" and work_item.status == "done":
        transition = "submitted"

    elif old_status == "done" and work_item.status != "done":
        transition = "submission_reverted"

    else:
        transition = "status_updated"

    # --------------------------------------------------
    # CONTENT
    # --------------------------------------------------
    title = "Work item status update"

    if transition == "submitted":
        message = (
            f"{actor_name} submitted a work item under "
            f"the work cycle \"{wc_title}\"."
        )
        priority = Notification.Priority.WARNING

        email_subject = "Work Item Submitted"
        email_body_text = (
            f"Good day.\n\n"
            f"{actor_name} has submitted a work item under the work cycle "
            f"\"{wc_title}\".\n\n"
            f"Please review the submission at your convenience.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day!
            </p>
            
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                <span style="font-size: 48px;">📤</span>
                <h2 style="margin: 12px 0 0 0; color: #1e40af; font-size: 20px;">New Submission</h2>
            </div>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                <strong>{actor_name}</strong> has submitted a work item under the work cycle 
                <strong>"{wc_title}"</strong>.
            </p>
            
            {format_info_box("Submitted By", actor_name, "👤")}
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("Status", "Submitted for Review", "📤")}
            
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    ⚠️ <strong>Action Required:</strong> Please review the submission at your convenience.
                </p>
            </div>
        """
        
        email_title = "📤 Work Item Submitted"

    elif transition == "submission_reverted":
        message = (
            f"{actor_name} reverted a previously submitted work item "
            f"under the work cycle \"{wc_title}\"."
        )
        priority = Notification.Priority.INFO

        email_subject = "Work Item Submission Reverted"
        email_body_text = (
            f"Good day.\n\n"
            f"{actor_name} has reverted a previously submitted work item "
            f"under the work cycle \"{wc_title}\".\n\n"
            f"This item is now editable again.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day!
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                <strong>{actor_name}</strong> has reverted a previously submitted work item 
                under the work cycle <strong>"{wc_title}"</strong>.
            </p>
            
            {format_info_box("User", actor_name, "👤")}
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("Status", "Submission Reverted", "↩️")}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    ℹ️ This item is now editable again by the user.
                </p>
            </div>
        """
        
        email_title = "↩️ Submission Reverted"

    else:
        new_label = dict(
            WorkItem._meta.get_field("status").choices
        ).get(work_item.status, work_item.status)

        message = (
            f"{actor_name} updated the status of a work item under "
            f"\"{wc_title}\" to \"{new_label}\"."
        )
        priority = Notification.Priority.INFO

        email_subject = "Work Item Status Updated"
        email_body_text = (
            f"Good day.\n\n"
            f"{actor_name} updated the status of a work item under "
            f"the work cycle \"{wc_title}\" to \"{new_label}\".\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day!
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                <strong>{actor_name}</strong> updated the status of a work item under 
                the work cycle <strong>"{wc_title}"</strong>.
            </p>
            
            {format_info_box("User", actor_name, "👤")}
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("New Status", new_label, "🔄")}
        """
        
        email_title = "🔄 Status Updated"

    # --------------------------------------------------
    # CREATE IN-APP NOTIFICATION (DEDUP SAFE)
    # --------------------------------------------------
    notif, created = Notification.objects.get_or_create(
        recipient=admin,
        category=Notification.Category.STATUS,
        work_item=work_item,
        title=f"{title}: {transition}",  # dedup key
        defaults={
            "priority": priority,
            "message": message,
            "workcycle": work_item.workcycle,
            "action_url": reverse(
                "admin_app:work-item-review",
                args=[work_item.id],
            ),
        },
    )

    # --------------------------------------------------
    # EMAIL (ONLY ON FIRST CREATE)
    # --------------------------------------------------
    if created and admin.email:
        email_body_html = get_styled_email_html(
            email_title, 
            content_html,
            action_url=f"/admin/work-items/{work_item.id}/review/",
            action_text="Review Work Item"
        )

        send_logged_email(
            recipient_email=admin.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="status",
            sender=actor,  # Add the actor as sender
            recipient=admin,
            fail_silently=True
        )
