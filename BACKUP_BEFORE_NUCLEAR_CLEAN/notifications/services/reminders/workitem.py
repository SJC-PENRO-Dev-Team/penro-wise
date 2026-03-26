"""
notifications/services/reminders/workitem.py

Scheduled reminders for WorkItem owners.
"""

from django.utils import timezone
from django.conf import settings

from accounts.models import WorkItem
from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)


WORKITEM_MILESTONES = {
    7: "7 days left",
    5: "5 days left",
    3: "3 days left",
    1: "1 day left",
    0: "Due today",
}


def send_workitem_deadline_reminders():
    """Sends deadline reminders for active work items."""
    today = timezone.localdate()
    notification_count = 0

    items = (
        WorkItem.objects
        .select_related("workcycle", "owner")
        .filter(is_active=True, workcycle__is_active=True, workcycle__due_at__date__gte=today)
    )

    for wi in items:
        due_date = wi.workcycle.due_at.date()
        days_remaining = (due_date - today).days

        if days_remaining not in WORKITEM_MILESTONES:
            continue
        if wi.status == "done" and days_remaining > 0:
            continue
        if not wi.owner.email:
            continue

        label = WORKITEM_MILESTONES[days_remaining]
        title = f"Work item due: {label}"
        user_name = wi.owner.get_full_name() or wi.owner.username

        if days_remaining > 0:
            day_word = "day" if days_remaining == 1 else "days"
            in_app_message = f'Your work item for "{wi.workcycle.title}" is due in {days_remaining} {day_word}.'
            priority = Notification.Priority.WARNING
        else:
            if wi.status == "done":
                in_app_message = f'Your work item for "{wi.workcycle.title}" was due today (submitted).'
            else:
                in_app_message = f'Your work item for "{wi.workcycle.title}" is due today.'
            priority = Notification.Priority.DANGER

        notification, created = Notification.objects.get_or_create(
            recipient=wi.owner, category=Notification.Category.REMINDER, work_item=wi, title=title,
            defaults={"priority": priority, "message": in_app_message, "workcycle": wi.workcycle}
        )
        notification_count += 1

        if not created:
            continue

        # Build email
        if days_remaining > 0:
            email_subject = "Reminder: Work Item Submission Deadline"
            email_body_text = (
                f"Good day, {user_name}.\n\n"
                f"This is a reminder regarding your assigned work item under the work cycle "
                f'"{wi.workcycle.title}".\n\n'
                f"The submission deadline is on {wi.workcycle.due_at:%A, %d %B %Y}.\n"
                f"Time remaining before the deadline: {label}.\n\n"
                f"Please ensure that the required work is completed and submitted within the prescribed period.\n\n"
                f"Access the system at: {SITE_URL}\n\n— PENRO WISE System"
            )
            
            urgency_color = "#fef3c7" if days_remaining > 1 else "#fee2e2"
            urgency_text_color = "#92400e" if days_remaining > 1 else "#991b1b"
            
            content_html = f"""
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                    Good day, <strong>{user_name}</strong>!
                </p>
                <div style="background: {urgency_color}; border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                    <span style="font-size: 48px;">⏰</span>
                    <h2 style="margin: 12px 0 0 0; color: {urgency_text_color}; font-size: 20px;">{label}</h2>
                </div>
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                    This is a reminder regarding your assigned work item under the work cycle 
                    <strong>"{wi.workcycle.title}"</strong>.
                </p>
                {format_info_box("Work Cycle", wi.workcycle.title, "📁")}
                {format_info_box("Due Date", wi.workcycle.due_at.strftime("%A, %d %B %Y"), "📅")}
                {format_info_box("Time Remaining", label, "⏰")}
                <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
                    <p style="margin: 0; color: #92400e; font-size: 14px;">
                        ⚠️ Please ensure that the required work is completed and submitted within the prescribed period.
                    </p>
                </div>
            """
            email_title = f"⏰ Reminder: {label}"
        else:
            if wi.status == "done":
                email_subject = "Notice: Work Item Submission Confirmed (Due Today)"
                email_body_text = (
                    f"Good day, {user_name}.\n\n"
                    f"This is to confirm that your work item under the work cycle "
                    f'"{wi.workcycle.title}" was due today, {wi.workcycle.due_at:%A, %d %B %Y}.\n\n'
                    f"Your submission has been recorded and is now pending review.\n\n"
                    f"Thank you for completing your assigned work within the deadline.\n\n"
                    f"Access the system at: {SITE_URL}\n\n— PENRO WISE System"
                )
                content_html = f"""
                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                        Good day, <strong>{user_name}</strong>!
                    </p>
                    <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                        <span style="font-size: 48px;">✅</span>
                        <h2 style="margin: 12px 0 0 0; color: #065f46; font-size: 20px;">Submitted on Time!</h2>
                    </div>
                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                        Your work item under the work cycle <strong>"{wi.workcycle.title}"</strong> was due today 
                        and your submission has been recorded.
                    </p>
                    {format_info_box("Work Cycle", wi.workcycle.title, "📁")}
                    {format_info_box("Status", "Submitted - Pending Review", "✅")}
                    <div style="background-color: #d1fae5; border-radius: 8px; padding: 16px; margin: 24px 0;">
                        <p style="margin: 0; color: #065f46; font-size: 14px;">
                            ✨ Thank you for completing your assigned work within the deadline!
                        </p>
                    </div>
                """
                email_title = "✅ Submission Confirmed"
            else:
                email_subject = "Notice: Work Item Submission Due Today"
                email_body_text = (
                    f"Good day, {user_name}.\n\n"
                    f"This is to inform you that the submission deadline for your assigned work item "
                    f'under the work cycle "{wi.workcycle.title}" is today, {wi.workcycle.due_at:%A, %d %B %Y}.\n\n'
                    f"Please ensure that the required submission is completed within the day.\n\n"
                    f"Access the system at: {SITE_URL}\n\n— PENRO WISE System"
                )
                content_html = f"""
                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                        Good day, <strong>{user_name}</strong>!
                    </p>
                    <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                        <span style="font-size: 48px;">🚨</span>
                        <h2 style="margin: 12px 0 0 0; color: #991b1b; font-size: 20px;">Due Today!</h2>
                    </div>
                    <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                        The submission deadline for your assigned work item under the work cycle 
                        <strong>"{wi.workcycle.title}"</strong> is <strong>today</strong>.
                    </p>
                    {format_info_box("Work Cycle", wi.workcycle.title, "📁")}
                    {format_info_box("Due Date", "TODAY - " + wi.workcycle.due_at.strftime("%A, %d %B %Y"), "🚨")}
                    <div style="background-color: #fee2e2; border-radius: 8px; padding: 16px; margin: 24px 0;">
                        <p style="margin: 0; color: #991b1b; font-size: 14px;">
                            ⚠️ <strong>Immediate Action Required:</strong> Please ensure that the required submission 
                            is completed within the day.
                        </p>
                    </div>
                """
                email_title = "🚨 Due Today!"

        email_body_html = get_styled_email_html(
            email_title, content_html,
            action_url="/user/work-items/",
            action_text="View My Work Items"
        )

        send_logged_email(
            recipient_email=wi.owner.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="reminder",
            recipient=wi.owner,
            fail_silently=not settings.DEBUG
        )

    return notification_count
