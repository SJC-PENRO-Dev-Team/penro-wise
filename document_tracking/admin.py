"""
Django Admin configuration for Document Tracking System.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Section, Submission, Logbook


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """Admin interface for Section model."""
    
    list_display = ['name', 'get_name_display', 'officers_count', 'created_at']
    list_filter = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    filter_horizontal = ['officers']
    
    fieldsets = (
        ('Section Information', {
            'fields': ('name', 'officers')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_name_display(self, obj):
        """Display human-readable section name."""
        return obj.get_name_display()
    get_name_display.short_description = 'Display Name'
    
    def officers_count(self, obj):
        """Count officers assigned to this section."""
        return obj.officers.count()
    officers_count.short_description = 'Officers'


class LogbookInline(admin.TabularInline):
    """Inline admin for Logbook entries."""
    
    model = Logbook
    extra = 0
    readonly_fields = ['timestamp', 'action', 'actor', 'old_status', 'new_status', 'remarks', 'file_names']
    can_delete = False
    
    fields = ['timestamp', 'action', 'actor', 'old_status', 'new_status', 'remarks']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin interface for Submission model."""
    
    list_display = [
        'id',
        'tracking_number_display',
        'title',
        'status_badge',
        'document_type',
        'submitted_by',
        'assigned_section',
        'created_at',
        'view_link'
    ]
    
    list_filter = [
        'status',
        'document_type',
        'assigned_section',
        'is_locked',
        'tracking_locked',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'tracking_number',
        'title',
        'purpose',
        'submitted_by__email',
        'submitted_by__first_name',
        'submitted_by__last_name'
    ]
    
    readonly_fields = [
        'tracking_number',
        'tracking_locked',
        'is_locked',
        'is_stored_in_file_manager',
        'submitted_by',
        'created_at',
        'updated_at',
        'primary_folder_link',
        'archive_folder_link',
        'file_manager_folder_link',
        'files_count',
        'logbook_count'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'tracking_number',
                'tracking_locked',
                'title',
                'document_type',
                'purpose'
            )
        }),
        ('Status & Assignment', {
            'fields': (
                'status',
                'assigned_section',
                'is_locked'
            )
        }),
        ('Submission Details', {
            'fields': (
                'submitted_by',
                'created_at',
                'updated_at'
            )
        }),
        ('File Management', {
            'fields': (
                'is_stored_in_file_manager',
                'primary_folder_link',
                'archive_folder_link',
                'file_manager_folder_link',
                'files_count'
            ),
            'classes': ('collapse',)
        }),
        ('Activity', {
            'fields': ('logbook_count',),
            'classes': ('collapse',)
        })
    )
    
    inlines = [LogbookInline]
    
    def tracking_number_display(self, obj):
        """Display tracking number with lock icon if locked."""
        if obj.tracking_number:
            if obj.tracking_locked:
                return format_html(
                    '<span style="color: #6b21a8; font-weight: 600;">{} <i class="fas fa-lock" style="color: #94a3b8;"></i></span>',
                    obj.tracking_number
                )
            return format_html(
                '<span style="color: #6b21a8; font-weight: 600;">{}</span>',
                obj.tracking_number
            )
        return format_html('<span style="color: #94a3b8; font-style: italic;">Not assigned</span>')
    tracking_number_display.short_description = 'Tracking #'
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending_tracking': '#f59e0b',
            'received': '#3b82f6',
            'under_review': '#8b5cf6',
            'for_compliance': '#f59e0b',
            'returned_to_sender': '#ef4444',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; display: inline-block;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def view_link(self, obj):
        """Link to view submission detail page."""
        url = reverse('document_tracking:admin_submission_detail', args=[obj.id])
        return format_html(
            '<a href="{}" style="color: #8b5cf6; font-weight: 600;" target="_blank">View <i class="fas fa-external-link-alt"></i></a>',
            url
        )
    view_link.short_description = 'Actions'
    
    def primary_folder_link(self, obj):
        """Link to primary folder in admin."""
        if obj.primary_folder:
            url = reverse('admin:structure_documentfolder_change', args=[obj.primary_folder.id])
            return format_html(
                '<a href="{}" target="_blank">Folder #{} <i class="fas fa-external-link-alt"></i></a>',
                url,
                obj.primary_folder.id
            )
        return '-'
    primary_folder_link.short_description = 'Primary Folder'
    
    def archive_folder_link(self, obj):
        """Link to archive folder in admin."""
        if obj.archive_folder:
            url = reverse('admin:structure_documentfolder_change', args=[obj.archive_folder.id])
            return format_html(
                '<a href="{}" target="_blank">Folder #{} <i class="fas fa-external-link-alt"></i></a>',
                url,
                obj.archive_folder.id
            )
        return '-'
    archive_folder_link.short_description = 'Archive Folder'
    
    def file_manager_folder_link(self, obj):
        """Link to file manager folder in admin."""
        if obj.file_manager_folder:
            url = reverse('admin:structure_documentfolder_change', args=[obj.file_manager_folder.id])
            return format_html(
                '<a href="{}" target="_blank">Folder #{} <i class="fas fa-external-link-alt"></i></a>',
                url,
                obj.file_manager_folder.id
            )
        return '-'
    file_manager_folder_link.short_description = 'File Manager Folder'
    
    def files_count(self, obj):
        """Count total files across all folders."""
        count = 0
        if obj.primary_folder:
            count += obj.primary_folder.files.count()
        if obj.archive_folder:
            count += obj.archive_folder.files.count()
        if obj.file_manager_folder:
            count += obj.file_manager_folder.files.count()
        return count
    files_count.short_description = 'Total Files'
    
    def logbook_count(self, obj):
        """Count logbook entries."""
        return obj.logs.count()
    logbook_count.short_description = 'Activity Entries'
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of locked submissions."""
        if obj and obj.is_locked:
            return False
        return super().has_delete_permission(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for locked submissions."""
        readonly = list(self.readonly_fields)
        if obj and obj.is_locked:
            readonly.extend(['status', 'assigned_section'])
        return readonly


@admin.register(Logbook)
class LogbookAdmin(admin.ModelAdmin):
    """Admin interface for Logbook model."""
    
    list_display = [
        'id',
        'submission_link',
        'action',
        'actor',
        'old_status',
        'new_status',
        'timestamp'
    ]
    
    list_filter = [
        'action',
        'old_status',
        'new_status',
        'timestamp'
    ]
    
    search_fields = [
        'submission__tracking_number',
        'submission__title',
        'actor__email',
        'actor__first_name',
        'actor__last_name',
        'remarks'
    ]
    
    readonly_fields = [
        'submission',
        'action',
        'old_status',
        'new_status',
        'remarks',
        'file_names',
        'actor',
        'timestamp'
    ]
    
    fieldsets = (
        ('Log Entry', {
            'fields': (
                'submission',
                'action',
                'old_status',
                'new_status',
                'remarks'
            )
        }),
        ('Files', {
            'fields': ('file_names',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'actor',
                'timestamp'
            )
        })
    )
    
    def submission_link(self, obj):
        """Link to submission."""
        url = reverse('document_tracking:admin_submission_detail', args=[obj.submission.id])
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            obj.submission.tracking_number or f'Submission #{obj.submission.id}'
        )
    submission_link.short_description = 'Submission'
    
    def has_add_permission(self, request):
        """Prevent manual creation of logbook entries."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of logbook entries."""
        return False


# Customize admin site header and title
admin.site.site_header = 'WISE Document Tracking Administration'
admin.site.site_title = 'Document Tracking Admin'
admin.site.index_title = 'Document Tracking System Management'
