"""
Notification API Views
======================

JSON API endpoints for the floating notification panel.
All endpoints require authentication and return JSON responses.
"""

import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Notification
from .utils import invalidate_notification_cache


class NotificationListAPI(LoginRequiredMixin, View):
    """
    GET /api/notifications/
    
    Returns paginated notifications for the current user.
    
    Query params:
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 10, max: 50)
        - unread_only (bool): Filter to unread only (default: false)
    
    Response:
        {
            "notifications": [...],
            "has_more": bool,
            "unread_count": int,
            "total_count": int
        }
    """
    
    def get(self, request):
        user = request.user
        
        # Parse query params
        try:
            page = max(1, int(request.GET.get("page", 1)))
            limit = min(50, max(1, int(request.GET.get("limit", 10))))
        except (ValueError, TypeError):
            page = 1
            limit = 10
        
        unread_only = request.GET.get("unread_only", "").lower() == "true"
        
        # Build queryset
        qs = (
            Notification.objects
            .filter(recipient=user)
            .select_related("work_item", "workcycle")
            .order_by("-created_at")
        )
        
        if unread_only:
            qs = qs.filter(is_read=False)
        
        # Pagination
        total_count = qs.count()
        offset = (page - 1) * limit
        notifications = list(qs[offset:offset + limit])
        has_more = (offset + limit) < total_count
        
        # Unread count (always return total unread)
        unread_count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
        # Serialize notifications
        data = {
            "notifications": [
                self._serialize_notification(n) for n in notifications
            ],
            "has_more": has_more,
            "unread_count": unread_count,
            "total_count": total_count,
            "page": page,
            "limit": limit,
        }
        
        return JsonResponse(data)
    
    def _serialize_notification(self, notif):
        """Serialize a notification to JSON-safe dict."""
        return {
            "id": notif.id,
            "category": notif.category,
            "priority": notif.priority,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat(),
            "read_at": notif.read_at.isoformat() if notif.read_at else None,
            "action_url": notif.action_url or self._get_default_action_url(notif),
            "work_item_id": notif.work_item_id,
            "workcycle_id": notif.workcycle_id,
        }
    
    def _get_default_action_url(self, notif):
        """Generate default action URL based on notification context."""
        # Work item takes priority
        if notif.work_item_id:
            # Determine URL based on user role
            if hasattr(notif.recipient, 'login_role'):
                if notif.recipient.login_role == "admin":
                    return f"/admin/work-items/{notif.work_item_id}/review/"
                return f"/user/work-items/{notif.work_item_id}/"
        
        # Workcycle URL (admin only typically)
        if notif.workcycle_id:
            if hasattr(notif.recipient, 'login_role'):
                if notif.recipient.login_role == "admin":
                    return f"/admin/workcycles/{notif.workcycle_id}/assignments/"
                # For users, link to their work items page
                return "/user/work-items/"
        
        return ""


class NotificationUnreadCountAPI(LoginRequiredMixin, View):
    """
    GET /api/notifications/unread-count/
    
    Returns the unread notification count for the current user.
    
    Response:
        {
            "unread_count": int
        }
    """
    
    def get(self, request):
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({"unread_count": unread_count})


@method_decorator(csrf_protect, name='dispatch')
class NotificationMarkReadAPI(LoginRequiredMixin, View):
    """
    POST /api/notifications/<id>/read/
    
    Marks a single notification as read.
    
    Response:
        {
            "success": bool,
            "unread_count": int
        }
    """
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
        except Notification.DoesNotExist:
            return JsonResponse(
                {"error": "Notification not found"},
                status=404
            )
        
        # Authorization check
        if notification.recipient_id != request.user.id:
            return JsonResponse(
                {"error": "You do not have permission to access this notification"},
                status=403
            )
        
        # Mark as read
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
            
            # Invalidate cache
            invalidate_notification_cache(request.user.id)
        
        # Get updated unread count
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        return JsonResponse({
            "success": True,
            "unread_count": unread_count
        })


@method_decorator(csrf_protect, name='dispatch')
class NotificationMarkAllReadAPI(LoginRequiredMixin, View):
    """
    POST /api/notifications/mark-all-read/
    
    Marks all notifications as read for the current user.
    
    Optional body (JSON):
        {
            "category": "review"  // Optional: only mark specific category
        }
    
    Response:
        {
            "success": bool,
            "marked_count": int,
            "unread_count": int
        }
    """
    
    def post(self, request):
        user = request.user
        
        # Parse optional category filter from body
        category = None
        if request.body:
            try:
                body = json.loads(request.body)
                category = body.get("category")
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Build queryset
        qs = Notification.objects.filter(
            recipient=user,
            is_read=False
        )
        
        if category:
            qs = qs.filter(category=category)
        
        # Bulk update
        now = timezone.now()
        marked_count = qs.update(
            is_read=True,
            read_at=now
        )
        
        # Invalidate cache
        invalidate_notification_cache(user.id)
        
        # Get updated unread count
        unread_count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
        return JsonResponse({
            "success": True,
            "marked_count": marked_count,
            "unread_count": unread_count
        })
