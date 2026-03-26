"""
Context Processors for User App
================================

Provides global template variables for unread discussion counts
using Facebook-style per-user read cursors.

Enable in settings.py:

TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                # ...
                "user_app.context_processors.unread_discussions_cached",
            ],
        },
    },
]
"""

from django.core.cache import cache

from accounts.models import (
    WorkItem,
    WorkItemMessage,
    WorkItemReadState,
)
def unread_discussions(request):
    """
    Add unread discussion count to all templates
    using cursor-based (Facebook-style) read receipts.

    Template usage:
        {% if has_unread_discussions %}
            <span class="badge">{{ unread_discussions_count }}</span>
        {% endif %}
    """

    if not request.user.is_authenticated:
        return {
            "unread_discussions_count": 0,
            "has_unread_discussions": False,
        }

    total_unread = 0

    work_items = (
        WorkItem.objects
        .filter(owner=request.user, is_active=True)
        .prefetch_related("messages", "read_states")
    )

    for item in work_items:
        read_state = next(
            (
                rs for rs in item.read_states.all()
                if rs.user_id == request.user.id
            ),
            None,
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        unread_count = (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )

        total_unread += unread_count

    return {
        "unread_discussions_count": total_unread,
        "has_unread_discussions": total_unread > 0,
    }
def unread_discussions_cached(request):
    """
    Cached unread discussion counter.

    - Facebook-style cursor logic
    - Per-user cache key
    - 60-second TTL
    - Requires explicit invalidation
    """

    if not request.user.is_authenticated:
        return {
            "unread_discussions_count": 0,
            "has_unread_discussions": False,
        }

    cache_key = f"unread_discussions_user_{request.user.id}"
    cached_value = cache.get(cache_key)

    if cached_value is not None:
        return {
            "unread_discussions_count": cached_value,
            "has_unread_discussions": cached_value > 0,
        }

    total_unread = 0

    work_items = (
        WorkItem.objects
        .filter(owner=request.user, is_active=True)
        .prefetch_related("messages", "read_states")
    )

    for item in work_items:
        read_state = next(
            (
                rs for rs in item.read_states.all()
                if rs.user_id == request.user.id
            ),
            None,
        )

        last_read_id = read_state.last_read_message_id if read_state else 0

        total_unread += (
            item.messages
            .filter(id__gt=last_read_id)
            .exclude(sender=request.user)
            .count()
        )

    # Cache for 60 seconds
    cache.set(cache_key, total_unread, timeout=60)

    return {
        "unread_discussions_count": total_unread,
        "has_unread_discussions": total_unread > 0,
    }
def invalidate_unread_cache(user):
    """
    Invalidate cached unread discussion count for a user.

    Call this when:
    - A new message is created
    - A discussion thread is opened (cursor moves)
    - "Mark all as read" is triggered
    - A work item is archived/deactivated
    """
    cache.delete(f"unread_discussions_user_{user.id}")


def user_unread_notifications(request):
    """
    Global unread notification count for USER.

    Uses cached count with 60-second TTL.

    Template usage:
        {% if has_unread_notifications %}
            <span class="badge">{{ unread_notifications_count }}</span>
        {% endif %}
    """
    from notifications.utils import get_unread_notification_count

    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "has_unread_notifications": False,
        }

    count = get_unread_notification_count(request.user.id)

    return {
        "unread_notifications_count": count,
        "has_unread_notifications": count > 0,
    }


def user_unread_emails(request):
    """
    Global unread email count for USER.

    Template usage:
        {% if has_unread_emails %}
            <span class="badge">{{ unread_emails_count }}</span>
        {% endif %}
    """
    from notifications.models import EmailLog

    if not request.user.is_authenticated:
        return {
            "unread_emails_count": 0,
            "has_unread_emails": False,
        }

    count = EmailLog.get_unread_count(request.user)

    return {
        "unread_emails_count": count,
        "has_unread_emails": count > 0,
    }
