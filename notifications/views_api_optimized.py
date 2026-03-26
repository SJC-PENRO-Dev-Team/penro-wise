"""
Optimized API views for notifications and counts.
These replace the context processors to reduce database load.
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from accounts.models import WorkItem
from notifications.models import Notification, EmailLog


@login_required
@cache_page(30)  # Cache for 30 seconds
def get_all_counts(request):
    """
    Get all counts in a single optimized query.
    Replaces 6 context processors with 1 cached API call.
    """
    user = request.user
    cache_key = f'counts_{user.id}_{user.login_role}'
    
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    
    # Calculate counts
    if user.login_role == 'admin':
        # Admin counts
        unread_discussions = _get_admin_unread_discussions(user)
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        unread_emails = EmailLog.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    else:
        # User counts
        unread_discussions = _get_user_unread_discussions(user)
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        unread_emails = EmailLog.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    
    data = {
        'unread_discussions': unread_discussions,
        'unread_notifications': unread_notifications,
        'unread_emails': unread_emails,
    }
    
    # Cache for 30 seconds
    cache.set(cache_key, data, 30)
    
    return JsonResponse(data)


def _get_user_unread_discussions(user):
    """Get unread discussion count for user."""
    work_items = WorkItem.objects.filter(
        owner=user,
        is_active=True
    ).prefetch_related("messages", "read_states")
    
    unread_count = 0
    for work_item in work_items:
        read_state = work_item.read_states.filter(user=user).first()
        last_read_id = read_state.last_read_message_id if read_state else 0
        
        unread_in_item = work_item.messages.filter(
            id__gt=last_read_id
        ).exclude(sender=user).count()
        
        if unread_in_item > 0:
            unread_count += 1
    
    return unread_count


def _get_admin_unread_discussions(user):
    """Get unread discussion count for admin."""
    work_items = WorkItem.objects.filter(
        is_active=True
    ).prefetch_related("messages", "read_states")
    
    unread_count = 0
    for work_item in work_items:
        read_state = work_item.read_states.filter(user=user).first()
        last_read_id = read_state.last_read_message_id if read_state else 0
        
        unread_in_item = work_item.messages.filter(
            id__gt=last_read_id
        ).exclude(sender=user).count()
        
        if unread_in_item > 0:
            unread_count += 1
    
    return unread_count


@login_required
def invalidate_counts_cache(request):
    """
    Invalidate the counts cache for the current user.
    Call this after actions that change counts (mark as read, new message, etc.)
    """
    user = request.user
    cache_key = f'counts_{user.id}_{user.login_role}'
    cache.delete(cache_key)
    
    return JsonResponse({'status': 'ok'})
