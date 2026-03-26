"""
Discussion Message Notification Service

Handles notifications for:
1. In-app notifications for every new discussion message
2. Bulk email notifications (digest) for unread messages

Channels:
- In-app notification (immediate, per message)
- Gmail SMTP email (bulk/digest only)

Author: System
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from notifications.models import Notification, EmailLog
from notifications.services.email_service import (
    send_logged_email,
    get_styled_email_html,
    format_info_box,
    SITE_URL,
)
from accounts.models import User, WorkItem, WorkItemMessage, WorkItemReadState


def notify_new_discussion_message(message_instance):
    """
    Create an in-app notification when a new discussion message is sent.
    
    Args:
        message_instance: The WorkItemMessage instance that was just created
    """
    work_item = message_instance.work_item
    sender = message_instance.sender
    
    # Determine the recipient (the other party in the discussion)
    if sender == work_item.owner:
        # User sent message → notify admins
        # Get all admins (or the workcycle creator specifically)
        recipients = User.objects.filter(login_role='admin', is_active=True)
    else:
        # Admin sent message → notify the work item owner
        recipients = [work_item.owner]
    
    sender_name = sender.get_full_name() or sender.username
    workcycle_title = work_item.workcycle.title if work_item.workcycle else "Work Item"
    
    # Truncate message for preview
    message_preview = message_instance.message[:100]
    if len(message_instance.message) > 100:
        message_preview += "..."
    
    # Create notification for each recipient
    for recipient in recipients:
        # Don't notify the sender
        if recipient == sender:
            continue
        
        # Determine the action URL based on recipient role
        # Navigate to the messages list page
        if recipient.login_role == 'admin':
            action_url = "/admin/discussions/"
        else:
            action_url = "/user/discussions/"
        
        Notification.objects.create(
            recipient=recipient,
            category=Notification.Category.MESSAGE,
            priority=Notification.Priority.INFO,
            title=f"New message from {sender_name}",
            message=f"In {workcycle_title}: \"{message_preview}\"",
            work_item=work_item,
            workcycle=work_item.workcycle,
            action_url=action_url
        )


def get_unread_messages_for_user(user):
    """
    Get all unread discussion messages for a user.
    
    Returns a dict with work_item_id as key and list of unread messages as value.
    """
    unread_by_work_item = {}
    
    if user.login_role == 'admin':
        # Admin sees all work items
        work_items = WorkItem.objects.filter(is_active=True).select_related('owner', 'workcycle')
    else:
        # User sees only their own work items
        work_items = WorkItem.objects.filter(owner=user, is_active=True).select_related('workcycle')
    
    for work_item in work_items:
        # Get user's read state
        read_state = WorkItemReadState.objects.filter(
            work_item=work_item,
            user=user
        ).first()
        
        last_read_id = read_state.last_read_message_id if read_state else 0
        
        # Get unread messages (not sent by this user)
        unread_messages = (
            WorkItemMessage.objects
            .filter(work_item=work_item, id__gt=last_read_id)
            .exclude(sender=user)
            .select_related('sender')
            .order_by('created_at')
        )
        
        if unread_messages.exists():
            unread_by_work_item[work_item.id] = {
                'work_item': work_item,
                'messages': list(unread_messages),
                'count': unread_messages.count(),
            }
    
    return unread_by_work_item


def send_bulk_message_digest_email(user, unread_data=None):
    """
    Send a bulk email digest of unread discussion messages to a user.
    
    Args:
        user: The User to send the digest to
        unread_data: Optional pre-fetched unread data (from get_unread_messages_for_user)
    
    Returns:
        EmailLog instance or None if no unread messages
    """
    if not user.email:
        return None
    
    if unread_data is None:
        unread_data = get_unread_messages_for_user(user)
    
    if not unread_data:
        return None
    
    total_unread = sum(item['count'] for item in unread_data.values())
    user_name = user.get_full_name() or user.username
    
    # Build plain text version
    email_subject = f"You have {total_unread} unread message{'s' if total_unread > 1 else ''} - PENRO WISE"
    
    text_lines = [
        f"Good day, {user_name}!",
        "",
        f"You have {total_unread} unread message{'s' if total_unread > 1 else ''} in your discussions.",
        "",
        "Summary:",
        ""
    ]
    
    for item_data in unread_data.values():
        work_item = item_data['work_item']
        messages = item_data['messages']
        count = item_data['count']
        
        workcycle_title = work_item.workcycle.title if work_item.workcycle else "Work Item"
        text_lines.append(f"• {workcycle_title}: {count} new message{'s' if count > 1 else ''}")
        
        # Show last 2 messages preview
        for msg in messages[-2:]:
            sender_name = msg.sender.get_full_name() or msg.sender.username
            preview = msg.message[:80] + "..." if len(msg.message) > 80 else msg.message
            text_lines.append(f"  - {sender_name}: \"{preview}\"")
        
        text_lines.append("")
    
    text_lines.extend([
        "Log in to view and respond to your messages.",
        f"Access the system at: {SITE_URL}",
        "",
        "Best regards,",
        "PENRO WISE Team"
    ])
    
    email_body_text = "\n".join(text_lines)
    
    # Build HTML version
    conversations_html = ""
    for item_data in unread_data.values():
        work_item = item_data['work_item']
        messages = item_data['messages']
        count = item_data['count']
        
        workcycle_title = work_item.workcycle.title if work_item.workcycle else "Work Item"
        
        # Build messages preview HTML
        messages_preview_html = ""
        for msg in messages[-3:]:  # Show last 3 messages
            sender_name = msg.sender.get_full_name() or msg.sender.username
            preview = msg.message[:100] + "..." if len(msg.message) > 100 else msg.message
            time_str = msg.created_at.strftime("%b %d, %I:%M %p")
            
            messages_preview_html += f"""
            <div style="background: #f8fafc; border-radius: 8px; padding: 12px; margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 600; color: #1e3a5f; font-size: 13px;">{sender_name}</span>
                    <span style="color: #94a3b8; font-size: 11px;">{time_str}</span>
                </div>
                <p style="margin: 0; color: #475569; font-size: 13px; line-height: 1.5;">{preview}</p>
            </div>
            """
        
        conversations_html += f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 16px; overflow: hidden;">
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 14px 16px; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: #0369a1; font-size: 14px;">📋 {workcycle_title}</span>
                    <span style="background: #ef4444; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                        {count} new
                    </span>
                </div>
            </div>
            <div style="padding: 12px 16px;">
                {messages_preview_html}
            </div>
        </div>
        """
    
    content_html = f"""
        <p style="color: #475569; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
            Good day, <strong>{user_name}</strong>!
        </p>
        
        <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
            <p style="margin: 0; color: #92400e; font-size: 15px;">
                📬 You have <strong>{total_unread} unread message{'s' if total_unread > 1 else ''}</strong> waiting for your response.
            </p>
        </div>
        
        <h3 style="color: #1e3a5f; font-size: 16px; margin: 24px 0 16px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px;">
            💬 Message Summary
        </h3>
        
        {conversations_html}
        
        <div style="text-align: center; margin: 32px 0 16px 0;">
            <p style="color: #64748b; font-size: 14px; margin: 0;">
                Log in to view and respond to your messages.
            </p>
        </div>
    """
    
    email_body_html = get_styled_email_html(f"📬 {total_unread} Unread Message{'s' if total_unread > 1 else ''}", content_html)
    
    return send_logged_email(
        recipient_email=user.email,
        subject=email_subject,
        body_text=email_body_text,
        body_html=email_body_html,
        email_type="notification",
        recipient=user,
        fail_silently=True
    )


def send_all_pending_message_digests():
    """
    Send bulk email digests to all users with unread messages.
    This should be called by a scheduled task (e.g., daily or hourly).
    
    Returns:
        dict with counts of emails sent
    """
    results = {
        'users_processed': 0,
        'emails_sent': 0,
        'emails_failed': 0,
        'users_skipped': 0,
    }
    
    # Get all active users with email addresses
    users = User.objects.filter(is_active=True).exclude(email='').exclude(email__isnull=True)
    
    for user in users:
        results['users_processed'] += 1
        
        unread_data = get_unread_messages_for_user(user)
        
        if not unread_data:
            results['users_skipped'] += 1
            continue
        
        email_log = send_bulk_message_digest_email(user, unread_data)
        
        if email_log:
            if email_log.status == 'sent':
                results['emails_sent'] += 1
            else:
                results['emails_failed'] += 1
        else:
            results['users_skipped'] += 1
    
    return results


def send_message_digest_to_user(user_id):
    """
    Send a message digest to a specific user.
    Useful for manual triggering or testing.
    
    Args:
        user_id: The ID of the user to send digest to
    
    Returns:
        EmailLog instance or None
    """
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return None
    
    return send_bulk_message_digest_email(user)
