"""
Notification URL Configuration
==============================

API endpoints for the notification panel.
"""

from django.urls import path

from .api_views import (
    NotificationListAPI,
    NotificationUnreadCountAPI,
    NotificationMarkReadAPI,
    NotificationMarkAllReadAPI,
)
from .views_api_optimized import get_all_counts, invalidate_counts_cache

app_name = "notifications"

urlpatterns = [
    # API Endpoints
    path(
        "api/notifications/",
        NotificationListAPI.as_view(),
        name="api-list"
    ),
    path(
        "api/notifications/unread-count/",
        NotificationUnreadCountAPI.as_view(),
        name="api-unread-count"
    ),
    path(
        "api/notifications/<int:pk>/read/",
        NotificationMarkReadAPI.as_view(),
        name="api-mark-read"
    ),
    path(
        "api/notifications/mark-all-read/",
        NotificationMarkAllReadAPI.as_view(),
        name="api-mark-all-read"
    ),
    # Optimized counts endpoint (replaces context processors)
    path(
        "api/counts/all/",
        get_all_counts,
        name="api-counts-all"
    ),
    path(
        "api/counts/invalidate/",
        invalidate_counts_cache,
        name="api-counts-invalidate"
    ),
]
