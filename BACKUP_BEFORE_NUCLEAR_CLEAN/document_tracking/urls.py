"""
URL configuration for Digital Document Tracking System.
"""
from django.urls import path

# Import main views from views.py module (use sys.modules to avoid circular import)
import sys
import os
import importlib.util

# Load views.py as a separate module to avoid circular import with views/ package
views_path = os.path.join(os.path.dirname(__file__), 'views.py')
spec = importlib.util.spec_from_file_location("document_tracking.main_views", views_path)
main_views = importlib.util.module_from_spec(spec)
sys.modules['document_tracking.main_views'] = main_views
spec.loader.exec_module(main_views)

# Import from views package subdirectories
from document_tracking.views import settings_views, api_views

app_name = 'document_tracking'

urlpatterns = [
    # User URLs
    path('submit/', main_views.submit_document, name='submit_document'),
    path('my-submissions/', main_views.my_submissions, name='my_submissions'),
    path('submission/<int:submission_id>/', main_views.submission_detail, name='submission_detail'),
    path('submission/<int:submission_id>/upload-compliance/', main_views.upload_compliance_files, name='upload_compliance_files'),
    
    # Admin URLs - ALL under /admin/submissions/ (plural)
    path('admin/submissions/', main_views.admin_submissions, name='admin_submissions'),
    path('admin/submissions/overview/', main_views.admin_overview, name='admin_overview'),
    path('admin/submissions/<int:submission_id>/', main_views.admin_submission_detail, name='admin_submission_detail'),
    path('admin/submissions/<int:submission_id>/assign-tracking/', main_views.assign_tracking, name='assign_tracking'),
    path('admin/submissions/<int:submission_id>/assign-section/', main_views.assign_section, name='assign_section'),
    path('admin/submissions/<int:submission_id>/change-status/', main_views.change_status, name='change_status'),
    path('admin/submissions/<int:submission_id>/reset-to-start/', main_views.reset_to_start, name='reset_to_start'),
    path('admin/submissions/<int:submission_id>/revert-workflow/', main_views.revert_workflow, name='revert_workflow'),
    path('admin/submissions/<int:submission_id>/undo-last-action/', main_views.undo_last_action, name='undo_last_action'),
    path('admin/submissions/<int:submission_id>/delete/', main_views.delete_submission, name='delete_submission'),
    
    # Settings URLs
    path('admin/settings/', settings_views.settings_index, name='settings'),
    path('admin/settings/document-types/', settings_views.document_types_list, name='document-types'),
    path('admin/settings/document-types/add/', settings_views.document_type_add, name='document-type-add'),
    path('admin/settings/document-types/<int:pk>/edit/', settings_views.document_type_edit, name='document-type-edit'),
    path('admin/settings/document-types/<int:pk>/delete/', settings_views.document_type_delete, name='document-type-delete'),
    path('admin/settings/document-types/reorder/', settings_views.document_types_reorder, name='document-types-reorder'),
    
    # Settings - Sections
    path('admin/settings/sections/', settings_views.sections_list, name='settings_sections'),
    path('admin/settings/sections/create/', settings_views.section_create, name='settings_section_create'),
    path('admin/settings/sections/<int:section_id>/edit/', settings_views.section_edit, name='settings_section_edit'),
    path('admin/settings/sections/<int:section_id>/delete/', settings_views.section_delete, name='settings_section_delete'),
    
    # API URLs
    path('api/generate-tracking-number/', api_views.api_generate_tracking_number, name='api-generate-tracking'),
    path('api/validate-tracking-number/', api_views.api_validate_tracking_number, name='api-validate-tracking'),
    path('api/document-types/', api_views.api_document_types, name='api-document-types'),
    path('api/check-serial-availability/', api_views.api_check_serial_availability, name='api-check-serial-availability'),
    
    # Section Officer URLs
    path('section/submissions/', main_views.section_submissions, name='section_submissions'),
    path('section/submissions/<int:submission_id>/update-status/', main_views.section_update_status, name='section_update_status'),
]
