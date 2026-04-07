"""
Email Service - Centralized email sending with logging

All emails sent through the system should use this service to ensure
proper logging and tracking.

Uses Brevo API instead of SMTP for better reliability on Render.

Author: System
"""

from django.conf import settings
from django.utils import timezone
from notifications.models import EmailLog
from accounts.models import User
from notifications.services.brevo_api_backend import send_email_via_brevo_api


def send_logged_email(
    recipient_email,
    subject,
    body_text,
    body_html="",
    email_type="other",
    sender=None,
    recipient=None,
    fail_silently=False
):
    """
    Send an email via Brevo API and log it to the database.
    
    Args:
        recipient_email: Email address of the recipient
        subject: Email subject line
        body_text: Plain text email body
        body_html: HTML email body (optional)
        email_type: Type of email (welcome, org_change, profile_update, etc.)
        sender: User who triggered the email (optional)
        recipient: User who receives the email (optional, auto-detected if possible)
        fail_silently: If True, don't raise exceptions on failure
    
    Returns:
        EmailLog instance
    """
    # Try to find recipient user if not provided
    if recipient is None and recipient_email:
        try:
            recipient = User.objects.get(email=recipient_email)
        except User.DoesNotExist:
            pass
    
    # Create log entry
    email_log = EmailLog.log_email(
        recipient_email=recipient_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        email_type=email_type,
        sender=sender,
        recipient=recipient,
        status="pending"
    )
    
    try:
        # Send email via Brevo API
        response = send_email_via_brevo_api(
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html if body_html else body_text
        )
        
        email_log.mark_sent()
        
    except Exception as e:
        email_log.mark_failed(str(e))
        if not fail_silently:
            raise
    
    return email_log


def send_bulk_logged_email(
    recipient_emails,
    subject,
    body_text,
    body_html="",
    email_type="other",
    sender=None,
    fail_silently=False
):
    """
    Send the same email to multiple recipients and log each one.
    
    Args:
        recipient_emails: List of email addresses
        subject: Email subject line
        body_text: Plain text email body
        body_html: HTML email body (optional)
        email_type: Type of email
        sender: User who triggered the email (optional)
        fail_silently: If True, don't raise exceptions on failure
    
    Returns:
        List of EmailLog instances
    """
    logs = []
    
    for email in recipient_emails:
        log = send_logged_email(
            recipient_email=email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            email_type=email_type,
            sender=sender,
            fail_silently=fail_silently
        )
        logs.append(log)
    
    return logs


SITE_URL = getattr(settings, "SITE_URL", "http://localhost:8000")


def get_styled_email_html(title, content_html, footer_text="PENRO WISE Team", action_url=None, action_text="Go to PENRO WISE"):
    """
    Wrap email content in a styled HTML template.
    
    Args:
        title: Email title/header
        content_html: Main content HTML
        footer_text: Footer text
        action_url: Optional URL for the action button (relative path or full URL)
        action_text: Text for the action button
    
    Returns:
        Complete HTML email string
    """
    # Build action button HTML if URL provided
    if action_url:
        if action_url.startswith('/'):
            full_url = f"{SITE_URL}{action_url}"
        else:
            full_url = action_url
        action_button_html = f"""
            <div style="text-align: center; margin: 32px 0 16px 0;">
                <a href="{full_url}" style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                    {action_text}
                </a>
            </div>
        """
    else:
        action_button_html = f"""
            <div style="text-align: center; margin: 32px 0 16px 0;">
                <a href="{SITE_URL}" style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 14px;">
                    Go to PENRO WISE
                </a>
            </div>
        """
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f6f9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 30px 40px; border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 600;">
                                {title}
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {content_html}
                            {action_button_html}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 24px 40px; border-radius: 0 0 12px 12px; border-top: 1px solid #e2e8f0;">
                            <p style="margin: 0; color: #64748b; font-size: 14px; text-align: center;">
                                Best regards,<br>
                                <strong style="color: #1e3a5f;">{footer_text}</strong>
                            </p>
                            <p style="margin: 16px 0 0 0; color: #94a3b8; font-size: 12px; text-align: center;">
                                This is an automated message from PENRO WISE Work Submission & Tracking Information System
                            </p>
                            <p style="margin: 12px 0 0 0; text-align: center;">
                                <a href="{SITE_URL}" style="color: #1e3a5f; font-size: 12px; text-decoration: none;">
                                    {SITE_URL}
                                </a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def format_info_box(label, value, icon="📌"):
    """Create a styled info box for email content."""
    return f"""
    <div style="background-color: #f8fafc; border-left: 4px solid #1e3a5f; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;">
        <span style="color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">{icon} {label}</span>
        <p style="margin: 4px 0 0 0; color: #1e293b; font-size: 15px; font-weight: 500;">{value}</p>
    </div>
    """


def format_list_items(items, bullet="•"):
    """Format a list of items for email content."""
    html = '<ul style="margin: 12px 0; padding-left: 20px;">'
    for item in items:
        html += f'<li style="color: #475569; font-size: 14px; margin: 6px 0;">{bullet} {item}</li>'
    html += '</ul>'
    return html
