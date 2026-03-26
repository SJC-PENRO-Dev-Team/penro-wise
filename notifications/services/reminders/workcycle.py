"""
notifications/services/reminders/workcycle.py

Work Cycle deadline reminders for admins.
"""

from django.utils import timezone
from django.conf import settings

from accounts.models import WorkCycle
from notifications.models import Notification
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL
)


WORKCYCLE_MILESTONES = {
    5: "5 days left",
    3: "3 days left",
    1: "1 day left",
    0: "Due today",
}


def send_workcycle_deadline_reminders():
    """Sends deadline reminders for active work cycles to admins."""
    today = timezone.localdate()
    notification_count = 0

    active_cycles = WorkCycle.objects.filter(
        is_active=True, due_at__date__gte=today, created_by__isnull=False
    )

    for wc in active_cycles:
        due_date = wc.due_at.date()
        days_remaining = (due_date - today).days

        if days_remaining not in WORKCYCLE_MILESTONES:
            continue

        label = WORKCYCLE_MILESTONES[days_remaining]
        title = f"Work cycle due: {label}"
        admin_name = wc.created_by.get_full_name() or wc.created_by.username

        if days_remaining > 0:
            day_word = "day" if days_remaining == 1 else "days"
            message = f'The work cycle "{wc.title}" you created is due in {days_remaining} {day_word}.'
            priority = Notification.Priority.WARNING
        else:
            message = f'The work cycle "{wc.title}" you created is due today.'
            priority = Notification.Priority.DANGER

        notification, created = Notification.objects.get_or_create(
            recipient=wc.created_by, category=Notification.Category.REMINDER, workcycle=wc, title=title,
            defaults={"priority": priority, "message": message}
        )
        notification_count += 1

        if not created or not wc.created_by.email:
            continue

        # Build email
        if days_remaining > 0:
            email_subject = "Reminder: Work Cycle Deadline (Administrative)"
            email_body_text = (
                f"Good day, {admin_name}.\n\n"
                f'This is a reminder that the work cycle "{wc.title}", which you created, '
                f"is scheduled for submission on {wc.due_at:%A, %d %B %Y}.\n\n"
                f"Time remaining before the deadline: {label}.\n\n"
                f"Access the system at: {SITE_URL}\n\n— PENRO WISE System"
            )
            
            urgency_color = "#fef3c7" if days_remaining > 1 else "#fee2e2"
            urgency_text_color = "#92400e" if days_remaining > 1 else "#991b1b"
            
            content_html = f"""
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                    Good day, <strong>{admin_name}</strong>!
                </p>
                <div style="background: {urgency_color}; border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                    <span style="font-size: 48px;">⏰</span>
                    <h2 style="margin: 12px 0 0 0; color: {urgency_text_color}; font-size: 20px;">{label}</h2>
                </div>
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                    This is a reminder that the work cycle <strong>"{wc.title}"</strong>, which you created, 
                    is approaching its deadline.
                </p>
                {format_info_box("Work Cycle", wc.title, "📁")}
                {format_info_box("Due Date", wc.due_at.strftime("%A, %d %B %Y"), "📅")}
                {format_info_box("Time Remaining", label, "⏰")}
            """
            email_title = f"⏰ Admin Reminder: {label}"
        else:
            email_subject = "Notice: Work Cycle Due Today (Administrative)"
            email_body_text = (
                f"Good day, {admin_name}.\n\n"
                f'This is to inform you that the work cycle "{wc.title}", which you created, '
                f"is due today, {wc.due_at:%A, %d %B %Y}.\n\n"
                f"Access the system at: {SITE_URL}\n\n— PENRO WISE System"
            )
            content_html = f"""
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                    Good day, <strong>{admin_name}</strong>!
                </p>
                <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-radius: 12px; padding: 20px; margin-bottom: 24px; text-align: center;">
                    <span style="font-size: 48px;">🚨</span>
                    <h2 style="margin: 12px 0 0 0; color: #991b1b; font-size: 20px;">Due Today!</h2>
                </div>
                <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                    The work cycle <strong>"{wc.title}"</strong>, which you created, is due <strong>today</strong>.
                </p>
                {format_info_box("Work Cycle", wc.title, "📁")}
                {format_info_box("Due Date", "TODAY - " + wc.due_at.strftime("%A, %d %B %Y"), "🚨")}
            """
            email_title = "🚨 Work Cycle Due Today!"

        email_body_html = get_styled_email_html(
            email_title, content_html,
            action_url="/admin/workcycles/",
            action_text="View Work Cycles"
        )

        send_logged_email(
            recipient_email=wc.created_by.email,
            subject=email_subject,
            body_text=email_body_text,
            body_html=email_body_html,
            email_type="reminder",
            recipient=wc.created_by,
            fail_silently=not settings.DEBUG
        )

    return notification_count
