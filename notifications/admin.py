from django.contrib import admin
from django.utils.html import format_html

from .models import Notification, EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for email logs
    """
    
    list_display = (
        "id",
        "recipient_email",
        "subject_preview",
        "email_type",
        "status_badge",
        "created_at",
    )
    
    list_filter = (
        "email_type",
        "status",
        "created_at",
    )
    
    search_fields = (
        "subject",
        "recipient_email",
        "sender_email",
        "recipient__username",
        "sender__username",
    )
    
    ordering = ("-created_at",)
    list_per_page = 25
    
    readonly_fields = (
        "created_at",
        "sent_at",
    )
    
    fieldsets = (
        ("Sender", {
            "fields": ("sender", "sender_email"),
        }),
        ("Recipient", {
            "fields": ("recipient", "recipient_email"),
        }),
        ("Content", {
            "fields": ("subject", "body_text", "body_html"),
        }),
        ("Classification", {
            "fields": ("email_type",),
        }),
        ("Status", {
            "fields": ("status", "error_message", "created_at", "sent_at"),
        }),
    )
    
    def subject_preview(self, obj):
        return obj.subject[:50] + "..." if len(obj.subject) > 50 else obj.subject
    subject_preview.short_description = "Subject"
    
    def status_badge(self, obj):
        colors = {
            "sent": "#16a34a",
            "failed": "#dc2626",
            "pending": "#f59e0b",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = "Status"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for system notifications
    (aligned with updated Notification model)
    """

    # =====================================================
    # LIST VIEW
    # =====================================================
    list_display = (
        "id",
        "recipient",
        "category",
        "priority",
        "colored_title",
        "is_read",
        "created_at",
    )

    list_filter = (
        "category",
        "priority",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "recipient__username",
        "recipient__first_name",
        "recipient__last_name",
    )

    ordering = ("-created_at",)
    list_per_page = 25

    # =====================================================
    # FIELDSETS (DETAIL VIEW)
    # =====================================================
    fieldsets = (
        ("Recipient", {
            "fields": ("recipient",),
        }),
        ("Classification", {
            "fields": ("category", "priority"),
        }),
        ("Content", {
            "fields": ("title", "message"),
        }),
        ("Context", {
            "fields": ("workcycle", "work_item", "action_url"),
        }),
        ("Status", {
            "fields": ("is_read", "read_at", "created_at"),
        }),
    )

    readonly_fields = (
        "created_at",
        "read_at",
    )

    # =====================================================
    # ACTIONS
    # =====================================================
    actions = (
        "mark_as_read",
        "mark_as_unread",
    )

    # =====================================================
    # CUSTOM DISPLAY HELPERS
    # =====================================================
    def colored_title(self, obj):
        """
        Color the title based on category for fast scanning.
        """
        color_map = {
            Notification.Category.REMINDER: "#f59e0b",    # orange
            Notification.Category.STATUS: "#16a34a",      # green
            Notification.Category.REVIEW: "#7c3aed",      # purple
            Notification.Category.ASSIGNMENT: "#2563eb",  # blue
            Notification.Category.MESSAGE: "#0ea5e9",     # sky
            Notification.Category.SYSTEM: "#6b7280",      # gray
        }

        color = color_map.get(obj.category, "#000000")

        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color,
            obj.title,
        )

    colored_title.short_description = "Title"

    # =====================================================
    # ADMIN ACTIONS
    # =====================================================
    @admin.action(description="Mark selected notifications as READ")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Mark selected notifications as UNREAD")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
