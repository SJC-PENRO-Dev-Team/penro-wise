from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from admin_app.views import (
    admin_work_item_discussion, user_profile,
    delete_workcycle, inactive_workcycle_list,  toggle_workcycle_archive,
    workcycle_list,  create_workcycle, edit_workcycle, reassign_workcycle, workcycle_assignments,  admin_delete_user, admin_reset_user_password,
    user_update_image, create_user, users, user_update_role, update_department, create_department, delete_department, user_update_department,
    completed_work_summary, done_workers_by_workcycle,
    review_work_item, admin_work_item_threads,
    # Hide/Unhide discussion views
    admin_hide_work_item_discussion, admin_hide_workcycle_discussions,
    admin_hide_user_thread, admin_unhide_discussion, admin_hidden_discussions,
)
# Removed: sections_by_division, services_by_section, units_by_parent, organization_views (Team/OrgAssignment removed)
from .views.dashboard_views import main_dashboard, workstate_overview
from .views.workcycle_views import workcycle_history
from .views.notification_views import admin_notifications, send_bulk_message_digests
from .views.email_logs_views import admin_email_logs, admin_email_detail
from .views.document_views import admin_documents
from .views.file_manager_views import (
    file_manager_view, create_folder, move_attachment, move_folder, 
    rename_folder, rename_attachment, delete_file, delete_folder, download_file, upload_files, bulk_move, bulk_delete,
    get_folder_structure, get_grouped_links
)
from .views.all_files_views import routed_documents_view, workstate_assets_view, bulk_download, bulk_delete_files, cleanup_missing_files, search_workstate_workcycles, search_workstate_files, get_workstate_assets
from .views.routed_documents_api import (
    search_submissions, search_tracking_numbers, search_tracking_numbers_filter, search_file_names, get_routed_documents_by_filter,
    search_document_types, search_document_status, search_sections
)
from .views.download_zip_views import download_selected_as_zip
from .views.file_viewer_views import preview_file, get_file_info, convert_docx_to_html, convert_excel_to_html, convert_pptx_to_html
from .views.api_views import api_workcycles, api_users, api_analytics
from .views.file_review_views import (
    accept_file, reject_file, undo_file_review,
    bulk_accept_files, bulk_reject_files
)
from .views.reviewed_files_views import rejected_files_list
from .views.pending_reviews_views import pending_reviews_list

app_name = "admin_app"


urlpatterns = [
    # Main Dashboard (central hub)
    path("", main_dashboard, name="main-dashboard"),
    
    # Workstate Overview (moved from root)
    path("workstate/", workstate_overview, name="workstate-overview"),
    
    # Legacy redirect for old dashboard URL
    path("dashboard/", main_dashboard, name="dashboard"),
    
    path("discussions/", admin_work_item_threads, name="discussion-list"),
    path("discussions/hidden/", admin_hidden_discussions, name="hidden-discussions"),
    path("discussions/<int:item_id>/hide/", admin_hide_work_item_discussion, name="hide-discussion"),
    path("discussions/workcycle/<int:workcycle_id>/hide/", admin_hide_workcycle_discussions, name="hide-workcycle-discussions"),
    path("discussions/workcycle/<int:workcycle_id>/user/<int:user_id>/hide/", admin_hide_user_thread, name="hide-user-thread"),
    path("discussions/unhide/<int:hidden_id>/", admin_unhide_discussion, name="unhide-discussion"),
    path("notifications/", admin_notifications, name="admin-notifications"),
    path("notifications/send-digests/", send_bulk_message_digests, name="send-message-digests"),
    path("email-logs/", admin_email_logs, name="email-logs"),
    path("api/email-logs/<int:email_id>/", admin_email_detail, name="email-detail"),

    # Workcycles
    path("workcycles/", workcycle_list, name="workcycles"),
    path("workcycles/inactive/", inactive_workcycle_list, name="inactive-workcycles"),
    path("workcycles/<int:pk>/history/", workcycle_history, name="workcycle-history"),
    path("workcycles/create/", create_workcycle, name="workcycle-create"),
    path("workcycles/edit/", edit_workcycle, name="workcycle-edit"),
    path("workcycles/reassign/", reassign_workcycle, name="workcycle-reassign"),
    path(
        "workcycles/<int:pk>/assignments/",
        workcycle_assignments,
        name="workcycle-assignments",
    ),
 path(
    "workcycles/<int:pk>/archive/",
    toggle_workcycle_archive,
    name="workcycle-archive",
),
    path(
        "workcycles/<int:pk>/delete/",
        delete_workcycle,
        name="workcycle-delete"
    ),

    # Analytics
    path(
        "analytics/completed-work/",
        completed_work_summary,
        name="completed-work-summary"
    ),
    path(
        "analytics/workcycle/<int:workcycle_id>/done-workers/",
        done_workers_by_workcycle,
        name="done-workers-by-workcycle"
    ),

    # Work Items
    path(
        "work-items/<int:item_id>/discussion/",
        admin_work_item_discussion,
        name="work-item-discussion"
    ),
    path(
        "work-items/<int:item_id>/review/",
        review_work_item,
        name="work-item-review"
    ),

    # Documents
    path(
        "documents/",
        admin_documents,
        name="documents"
    ),
    path(
        "documents/pending-reviews/",
        pending_reviews_list,
        name="pending-reviews"
    ),
    path(
        "documents/file-manager/",
        file_manager_view,
        name="file-manager"
    ),
    path(
        "documents/files/<int:folder_id>/",
        file_manager_view,
        name="file-manager-folder"
    ),
    path("documents/files/create-folder/", create_folder, name="create-folder"),
    path("documents/files/rename-folder/", rename_folder, name="rename-folder"),
    path("documents/files/rename-attachment/", rename_attachment, name="rename-attachment"),
    path("documents/files/delete-folder/", delete_folder, name="delete-folder"),
    path("documents/files/delete-file/", delete_file, name="delete-file"),
    path("documents/files/folder-structure/<int:folder_id>/", get_folder_structure, name="folder-structure"),
    path("documents/files/grouped-links/<int:folder_id>/<str:group_name>/", get_grouped_links, name="grouped-links"),
    path("documents/files/download/<int:attachment_id>/", download_file, name="download-file"),
    path("documents/files/preview/<int:attachment_id>/", preview_file, name="preview-file"),
    path("documents/files/info/<int:attachment_id>/", get_file_info, name="file-info"),
    path("documents/files/convert-docx/<int:attachment_id>/", convert_docx_to_html, name="convert-docx"),
    path("documents/files/convert-excel/<int:attachment_id>/", convert_excel_to_html, name="convert-excel"),
    path("documents/files/convert-pptx/<int:attachment_id>/", convert_pptx_to_html, name="convert-pptx"),
    path("documents/files/download-zip/", download_selected_as_zip, name="download-zip"),
    path("documents/files/upload/", upload_files, name="upload-files"),
    path("documents/files/move/", move_attachment, name="move-attachment"),
    path("documents/files/move-folder/", move_folder, name="move-folder"),
    path("documents/files/bulk-move/", bulk_move, name="bulk-move"),
    path("documents/files/bulk-delete/", bulk_delete, name="bulk-delete"),
    path("documents/files/bulk-download-all/", bulk_download, name="bulk-download"),
    path("documents/files/bulk-delete-all/", bulk_delete_files, name="bulk-delete-all"),
    path("documents/files/cleanup-missing/", cleanup_missing_files, name="cleanup-missing"),

    path(
        "documents/routed-documents/",
        routed_documents_view,
        name="routed-documents"
    ),
    path(
        "documents/workstate-assets/",
        workstate_assets_view,
        name="workstate-assets"
    ),

    path(
        "documents/rejected-files/",
        rejected_files_list,
        name="rejected-files"
    ),

    # Users
    path("users/", users, name="users"),
    path("users/create/", create_user, name="user-create"),
    path("users/department/create/", create_department, name="create-department"),
    path("users/department/<int:department_id>/update/", update_department, name="update-department"),
    path("users/department/<int:department_id>/delete/", delete_department, name="delete-department"),
    path("users/<int:user_id>/", user_profile, name="user-profile"),
    path("users/<int:user_id>/update-role/", user_update_role, name="user-update-role"),
    path("users/<int:user_id>/update-image/", user_update_image, name="user-update-image"),
    path("users/<int:user_id>/department/update/", user_update_department, name="user-update-department"),
    path(
        "users/<int:user_id>/reset-password/",
        admin_reset_user_password,
        name="user-reset-password"
    ),
    path(
        "users/<int:user_id>/delete/",
        admin_delete_user,
        name="user-delete"
    ),

    # Real-time filtering APIs
    path("api/workcycles/", api_workcycles, name="api-workcycles"),
    path("api/users/", api_users, name="api-users"),
    path("api/analytics/", api_analytics, name="api-analytics"),
    
    # Routed Documents APIs
    path("api/search-submissions/", search_submissions, name="api-search-submissions"),
    path("api/search-tracking/", search_tracking_numbers, name="api-search-tracking"),
    path("api/search-tracking-filter/", search_tracking_numbers_filter, name="api-search-tracking-filter"),
    path("api/search-files/", search_file_names, name="api-search-files"),
    path("api/search-document-types/", search_document_types, name="api-search-document-types"),
    path("api/search-document-status/", search_document_status, name="api-search-document-status"),
    path("api/search-sections/", search_sections, name="api-search-sections"),
    path("api/routed-documents/", get_routed_documents_by_filter, name="api-routed-documents"),
    
    # Workstate Assets APIs
    path("api/search-workstate-workcycles/", search_workstate_workcycles, name="api-search-workstate-workcycles"),
    path("api/search-workstate-files/", search_workstate_files, name="api-search-workstate-files"),
    path("api/workstate-assets/", get_workstate_assets, name="api-workstate-assets"),

    # File Review APIs
    path("api/files/<int:attachment_id>/accept/", accept_file, name="accept-file"),
    path("api/files/<int:attachment_id>/reject/", reject_file, name="reject-file"),
    path("api/files/<int:attachment_id>/undo/", undo_file_review, name="undo-file-review"),
    path("api/files/bulk-accept/", bulk_accept_files, name="bulk-accept-files"),
    path("api/files/bulk-reject/", bulk_reject_files, name="bulk-reject-files"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)