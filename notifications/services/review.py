from django.conf import settings
from django.urls import reverse

from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)
from accounts.models import WorkItem


# ============================================================
# WORK ITEM REVIEW DECISION CHANGED (ADMIN → USER)
# ============================================================

def notify_work_item_review_changed(
    *,
    work_item: WorkItem,
    actor,
    old_decision: str | None,
):
    """
    Notify the work item OWNER when an admin
    changes the review decision.

    Triggers on:
    - approved
    - revision
    - pending (only if reverted)

    Channels:
    - In-app notification
    - Email (SMTP with HTML)

    Dedup:
    - Per decision change
    """

    # --------------------------------------------------
    # SAFETY GUARDS
    # --------------------------------------------------
    if not work_item.owner:
        return

    if old_decision == work_item.review_decision:
        return

    if work_item.review_decision not in {"approved", "revision", "pending"}:
        return

    user = work_item.owner
    user_name = user.get_full_name() or user.username
    wc_title = work_item.workcycle.title

    decision_label = dict(
        WorkItem._meta.get_field("review_decision").choices
    ).get(work_item.review_decision, work_item.review_decision)

    # --------------------------------------------------
    # CONTENT
    # --------------------------------------------------
    title = "Work item review updated"

    if work_item.review_decision == "approved":
        message = (
            f"Your submitted work item under the work cycle "
            f"\"{wc_title}\" has been approved."
        )
        priority = Notification.Priority.INFO

    elif work_item.review_decision == "revision":
        message = (
            f"Your submitted work item under the work cycle "
            f"\"{wc_title}\" requires revision."
        )
        priority = Notification.Priority.WARNING

    else:  # reverted to pending
        message = (
            f"The review status of your work item under "
            f"\"{wc_title}\" has been reverted to pending."
        )
        priority = Notification.Priority.INFO

    # --------------------------------------------------
    # CREATE IN-APP NOTIFICATION
    # --------------------------------------------------
    notification = Notification.objects.create(
        recipient=user,
        category=Notification.Category.REVIEW,
        priority=priority,
        title=title,
        message=message,
        work_item=work_item,
        workcycle=work_item.workcycle,
        action_url=reverse(
            "user_app:work-item-detail",
            args=[work_item.id],
        ),
    )

    # --------------------------------------------------
    # EMAIL (FORMAL / GOVERNMENT STYLE WITH HTML)
    # --------------------------------------------------
    if not user.email:
        return

    if work_item.review_decision == "approved":
        email_subject = "Notice: Work Item Approved"
        email_body_text = (
            f"Good day, {user_name}.\n\n"
            f"This is to inform you that your submitted work item under the work cycle "
            f"\"{wc_title}\" has been approved.\n\n"
            f"No further action is required at this time.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                <span style="font-size: 48px;">✅</span>
                <h2 style="margin: 12px 0 0 0; color: #065f46; font-size: 20px;">Work Item Approved!</h2>
            </div>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your submitted work item under the work cycle <strong>"{wc_title}"</strong> 
                has been reviewed and approved.
            </p>
            
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("Status", "Approved", "✅")}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    ✨ No further action is required at this time. Thank you for your submission!
                </p>
            </div>
        """
        
        email_title = "✅ Work Item Approved"

    elif work_item.review_decision == "revision":
        email_subject = "Action Required: Work Item Needs Revision"
        email_body_text = (
            f"Good day, {user_name}.\n\n"
            f"Your submitted work item under the work cycle "
            f"\"{wc_title}\" has been reviewed and requires revision.\n\n"
            f"Please log in to the system to review the remarks and "
            f"resubmit accordingly.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>.
            </p>
            
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                <span style="font-size: 48px;">📝</span>
                <h2 style="margin: 12px 0 0 0; color: #92400e; font-size: 20px;">Revision Required</h2>
            </div>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                Your submitted work item under the work cycle <strong>"{wc_title}"</strong> 
                has been reviewed and requires revision.
            </p>
            
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("Status", "Needs Revision", "📝")}
            
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #92400e; font-size: 14px;">
                    ⚠️ <strong>Action Required:</strong> Please log in to the system to review 
                    the remarks and resubmit accordingly.
                </p>
            </div>
        """
        
        email_title = "📝 Revision Required"

    else:
        email_subject = "Notice: Work Item Review Reverted"
        email_body_text = (
            f"Good day, {user_name}.\n\n"
            f"The review status of your submitted work item under "
            f"\"{wc_title}\" has been reverted to pending.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"This notice is issued for your information.\n\n"
            f"— PENRO WISE System"
        )
        
        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>.
            </p>
            
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                The review status of your submitted work item under the work cycle 
                <strong>"{wc_title}"</strong> has been reverted to pending.
            </p>
            
            {format_info_box("Work Cycle", wc_title, "📁")}
            {format_info_box("Status", "Pending Review", "⏳")}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    ℹ️ This notice is issued for your information.
                </p>
            </div>
        """
        
        email_title = "⏳ Review Status Reverted"

    email_body_html = get_styled_email_html(
        email_title, 
        content_html,
        action_url=f"/user/work-items/{work_item.id}/",
        action_text="View Work Item"
    )

    send_logged_email(
        recipient_email=user.email,
        subject=email_subject,
        body_text=email_body_text,
        body_html=email_body_html,
        email_type="review",
        recipient=user,
        fail_silently=True
    )
