from django.contrib.auth import get_user_model
from django.conf import settings

from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)

User = get_user_model()


# ============================================================
# ASSIGNMENT NOTIFICATIONS (IN-APP + EMAIL)
# ============================================================

def create_assignment_notifications(
    *,
    user_ids,
    workcycle,
    assigned_by=None,
):
    """
    ASSIGNMENT notifications
    ------------------------
    - In-app notification (bulk)
    - One-time Gmail email per user (with HTML)
    """

    users = User.objects.filter(
        id__in=user_ids,
        is_active=True,
    )

    # -----------------------------
    # IN-APP NOTIFICATIONS (BULK)
    # -----------------------------
    Notification.objects.bulk_create([
        Notification(
            recipient=user,
            category=Notification.Category.ASSIGNMENT,
            priority=Notification.Priority.INFO,
            title="New work assigned",
            message=(
                f"You have been assigned to the work cycle "
                f'"{workcycle.title}".'
            ),
            workcycle=workcycle,
            action_url="/user/work-items/",
        )
        for user in users
    ])

    # -----------------------------
    # EMAIL NOTIFICATIONS (PER USER)
    # -----------------------------
    for user in users:
        if not user.email:
            continue

        user_name = user.get_full_name() or user.username
        subject = "Notice: New Work Cycle Assignment"

        # Plain text version
        body_text = (
            f"Good day, {user_name}.\n\n"
            f"This is to inform you that you have been assigned to the work cycle "
            f'"{workcycle.title}".\n\n'
            f"Please log in to the system to review the details, requirements, "
            f"and applicable deadlines associated with this assignment.\n\n"
        )

        if assigned_by:
            body_text += f"This assignment was issued by {assigned_by}.\n\n"

        body_text += (
            f"This notice is issued for your information and appropriate action.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"— PENRO WISE System"
        )

        # HTML version
        assigned_by_html = ""
        if assigned_by:
            assigned_by_html = f"""
            <p style="color: #64748b; font-size: 14px; margin: 16px 0 0 0;">
                This assignment was issued by: <strong>{assigned_by}</strong>
            </p>
            """

        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>!
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                This is to inform you that you have been assigned to a new work cycle.
            </p>
            
            <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
                📋 Assignment Details
            </h3>
            {format_info_box("Work Cycle", workcycle.title, "📁")}
            {format_info_box("Due Date", workcycle.due_at.strftime("%A, %d %B %Y") if workcycle.due_at else "Not specified", "📅")}
            
            {assigned_by_html}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    💡 Please log in to the system to review the details, requirements, 
                    and applicable deadlines associated with this assignment.
                </p>
            </div>
        """

        body_html = get_styled_email_html(
            "📋 New Work Cycle Assignment", 
            content_html,
            action_url="/user/work-items/",
            action_text="View My Work Items"
        )

        send_logged_email(
            recipient_email=user.email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            email_type="assignment",
            recipient=user,
            fail_silently=True
        )


# ============================================================
# REMOVAL NOTIFICATIONS (IN-APP + EMAIL)
# ============================================================

def create_removal_notifications(
    *,
    user_ids,
    workcycle,
    reason=None,
):
    """
    SYSTEM notifications
    --------------------
    - In-app notification (bulk)
    - One-time Gmail email per user (with HTML)
    """

    users = User.objects.filter(
        id__in=user_ids,
        is_active=True,
    )

    in_app_message = (
        reason
        or f'You were removed from the work cycle "{workcycle.title}".'
    )

    # -----------------------------
    # IN-APP NOTIFICATIONS (BULK)
    # -----------------------------
    Notification.objects.bulk_create([
        Notification(
            recipient=user,
            category=Notification.Category.SYSTEM,
            priority=Notification.Priority.WARNING,
            title="Work assignment changed",
            message=in_app_message,
            workcycle=workcycle,
            action_url="/user/work-items/",
        )
        for user in users
    ])

    # -----------------------------
    # EMAIL NOTIFICATIONS (PER USER)
    # -----------------------------
    for user in users:
        if not user.email:
            continue

        user_name = user.get_full_name() or user.username
        subject = "Notice: Work Cycle Assignment Update"

        # Plain text version
        body_text = (
            f"Good day, {user_name}.\n\n"
            f"This is to inform you that your assignment under the work cycle "
            f'"{workcycle.title}" has been updated and you are no longer included '
            f"in the said work cycle.\n\n"
        )

        if reason:
            body_text += f"Reason:\n{reason}\n\n"

        body_text += (
            f"If you require clarification or believe this update was made in error, "
            f"please coordinate with the appropriate administrator.\n\n"
            f"Access the system at: {SITE_URL}\n\n"
            f"This notice is issued for your information.\n\n"
            f"— PENRO WISE System"
        )

        # HTML version
        reason_html = ""
        if reason:
            reason_html = f"""
            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <p style="margin: 0 0 8px 0; color: #92400e; font-size: 13px; font-weight: 600;">Reason:</p>
                <p style="margin: 0; color: #92400e; font-size: 14px;">{reason}</p>
            </div>
            """

        content_html = f"""
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                Good day, <strong>{user_name}</strong>.
            </p>
            <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                This is to inform you that your assignment under the work cycle 
                <strong>"{workcycle.title}"</strong> has been updated and you are no longer 
                included in the said work cycle.
            </p>
            
            {reason_html}
            
            <div style="background-color: #f0f9ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
                <p style="margin: 0; color: #0369a1; font-size: 14px;">
                    💡 If you require clarification or believe this update was made in error, 
                    please coordinate with the appropriate administrator.
                </p>
            </div>
        """

        body_html = get_styled_email_html(
            "⚠️ Work Cycle Assignment Update", 
            content_html
        )

        send_logged_email(
            recipient_email=user.email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            email_type="assignment",
            recipient=user,
            fail_silently=True
        )
