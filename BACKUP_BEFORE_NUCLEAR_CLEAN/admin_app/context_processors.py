# admin_app/context_processors.py

from django.core.cache import cache

from accounts.models import (
    WorkItem,
    WorkItemReadState,
)
from notifications.utils import get_unread_notification_count


def admin_unread_discussions(request):
    """
    Global unread discussion count for ADMIN.

    Uses Facebook-style cursor-based read receipts.

    Template usage:
        {% if admin_has_unread_discussions %}
            <span class="badge">{{ admin_unread_discussions_count }}</span>
        {% endif %}
    """

    if not request.user.is_authenticated:
        return {
            "admin_unread_discussions_count": 0,
            "admin_has_unread_discussions": False,
        }

    total_unread = 0

    work_items = (
        WorkItem.objects
        .filter(is_active=True)
        .prefetch_related("messages", "read_states")
    )

    for item in work_items:
        # --------------------------------------------
        # READ CURSOR FOR THIS ADMIN
        # --------------------------------------------
        read_state = next(
            (
                rs for rs in item.read_states.all()
                if rs.user_id == request.user.id
            ),
            None,
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        # --------------------------------------------
        # UNREAD COUNT (OTHER PARTY ONLY)
        # --------------------------------------------
        unread = (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )

        total_unread += unread

    return {
        "admin_unread_discussions_count": total_unread,
        "admin_has_unread_discussions": total_unread > 0,
    }


def admin_unread_notifications(request):
    """
    Global unread notification count for ADMIN.

    Uses cached count with 60-second TTL.

    Template usage:
        {% if admin_has_unread_notifications %}
            <span class="badge">{{ admin_unread_notifications_count }}</span>
        {% endif %}
    """

    if not request.user.is_authenticated:
        return {
            "admin_unread_notifications_count": 0,
            "admin_has_unread_notifications": False,
        }

    count = get_unread_notification_count(request.user.id)

    return {
        "admin_unread_notifications_count": count,
        "admin_has_unread_notifications": count > 0,
    }


def admin_unread_emails(request):
    """
    Global unread email count for ADMIN.

    Template usage:
        {% if admin_has_unread_emails %}
            <span class="badge">{{ admin_unread_emails_count }}</span>
        {% endif %}
    """
    from notifications.models import EmailLog

    if not request.user.is_authenticated:
        return {
            "admin_unread_emails_count": 0,
            "admin_has_unread_emails": False,
        }

    count = EmailLog.get_unread_count(request.user)

    return {
        "admin_unread_emails_count": count,
        "admin_has_unread_emails": count > 0,
    }
