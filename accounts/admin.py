from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Q
from accounts.forms import WorkforcesDepartmentForm
    
from .models import (
    User,
    WorkforcesDepartment,
    WorkCycle,
    WorkAssignment,
    WorkItem,
    WorkItemAttachment,
    WorkItemMessage,
)

# ============================================================
# USER ADMIN
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("username",)

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "position_title",
        "login_role",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "login_role",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Work Information", {
            "fields": (
                "position_title",
                "login_role",
            )
        }),
    )


# ============================================================
# WORKFORCES DEPARTMENT
# ============================================================

@admin.register(WorkforcesDepartment)
class WorkforcesDepartmentAdmin(admin.ModelAdmin):
    form = WorkforcesDepartmentForm
    list_display = (
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# ============================================================
# PLANNING (WHAT & WHEN)
# ============================================================

@admin.register(WorkCycle)
class WorkCycleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "due_at",
        "is_active",
        "created_by",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "title",
    )

    autocomplete_fields = (
        "created_by",
    )

    date_hierarchy = "due_at"


@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "workcycle",
        "assigned_user",
        "assigned_department",
        "assigned_at",
    )

    list_filter = (
        "assigned_at",
    )

    autocomplete_fields = (
        "workcycle",
        "assigned_user",
        "assigned_department",
    )


# ============================================================
# EXECUTION (WORK ITEMS)
# ============================================================

class WorkItemAttachmentInline(admin.TabularInline):
    model = WorkItemAttachment
    extra = 0
    readonly_fields = ("uploaded_at",)
    autocomplete_fields = ("folder", "uploaded_by")


class WorkItemMessageInline(admin.TabularInline):
    model = WorkItemMessage
    extra = 0
    readonly_fields = ("created_at",)
    autocomplete_fields = ("sender",)


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = (
        "workcycle",
        "owner",
        "status",
        "review_decision",
        "is_active",
        "created_at",
    )

    list_filter = (
        "status",
        "review_decision",
        "is_active",
    )

    search_fields = (
        "workcycle__title",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    )

    autocomplete_fields = (
        "workcycle",
        "owner",
    )

    inlines = (
        WorkItemAttachmentInline,
        WorkItemMessageInline,
    )


@admin.register(WorkItemAttachment)
class WorkItemAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "work_item",
        "attachment_type",
        "uploaded_by",
        "uploaded_at",
    )

    list_filter = (
        "attachment_type",
    )

    autocomplete_fields = (
        "work_item",
        "folder",
        "uploaded_by",
    )


@admin.register(WorkItemMessage)
class WorkItemMessageAdmin(admin.ModelAdmin):
    list_display = (
        "work_item",
        "sender",
        "sender_role",
        "created_at",
    )

    list_filter = (
        "sender_role",
    )

    autocomplete_fields = (
        "work_item",
        "sender",
    )
