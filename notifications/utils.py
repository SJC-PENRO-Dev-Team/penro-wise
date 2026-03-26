"""
Notification Utilities
======================

Helper functions for notification management.
"""

from django.core.cache import cache


# ============================================================
# CACHE KEYS
# ============================================================

def get_notification_cache_key(user_id):
    """Get the cache key for a user's unread notification count."""
    return f"unread_notif_user_{user_id}"


# ============================================================
# CACHE MANAGEMENT
# ============================================================

def invalidate_notification_cache(user_id):
    """
    Invalidate the cached unread notification count for a user.
    
    Call this when:
    - A new notification is created for the user
    - A notification is marked as read
    - Notifications are bulk marked as read
    - A notification is deleted
    """
    cache_key = get_notification_cache_key(user_id)
    cache.delete(cache_key)


def get_unread_notification_count(user_id, use_cache=True):
    """
    Get the unread notification count for a user.
    
    Args:
        user_id: The user's ID
        use_cache: Whether to use cached value (default: True)
    
    Returns:
        int: The number of unread notifications
    """
    from .models import Notification
    
    cache_key = get_notification_cache_key(user_id)
    
    if use_cache:
        cached_count = cache.get(cache_key)
        if cached_count is not None:
            return cached_count
    
    # Query database
    count = Notification.objects.filter(
        recipient_id=user_id,
        is_read=False
    ).count()
    
    # Cache for 60 seconds
    cache.set(cache_key, count, timeout=60)
    
    return count


def invalidate_notification_cache_for_users(user_ids):
    """
    Invalidate notification cache for multiple users.
    
    Useful when bulk creating notifications.
    
    Args:
        user_ids: List or set of user IDs
    """
    for user_id in user_ids:
        invalidate_notification_cache(user_id)
