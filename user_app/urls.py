# user_app/urls.py

from django.urls import path

from .views.dashboard_views import main_dashboard, workstate_overview, dashboard

from .views.work_item_views import (
    user_work_items,
    user_inactive_work_items,
    user_work_item_detail,
    user_work_item_attachments,
    delete_work_item_attachment,
    toggle_work_item_archive,
    get_grouped_links,
)

from .views.user_work_item_threads import user_work_item_threads
from .views.notification_views import user_notifications
from .views.email_logs_views import user_email_logs, user_email_detail
from .views.user_profile_views import user_profile, user_update_image, user_reset_password
# Import message views
from .views.message_views import (
    user_work_item_discussion,
    user_discussions_list,
    user_mark_all_discussions_read,
    user_discussion_stats,
    hide_discussion,
    unhide_discussion,
    hidden_discussions_list,
)
from .views.reviewed_files_views import user_accepted_files, user_rejected_files
# Import shared file manager views from admin_app
from admin_app.views.file_manager_views import file_manager_view, download_file, get_grouped_links as get_file_manager_grouped_links
from admin_app.views.download_zip_views import download_selected_as_zip
# Import file viewer views
from admin_app.views.file_viewer_views import preview_file, get_file_info, convert_docx_to_html, convert_excel_to_html, convert_pptx_to_html

app_name = "user_app"


urlpatterns = [
    # ======================
    # DASHBOARD
    # ======================
    path("", main_dashboard, name="main-dashboard"),  # Main dashboard at /user/
    path("dashboard/", dashboard, name="dashboard"),  # Legacy URL - redirects to workstate overview
    path("workstate/", workstate_overview, name="workstate-overview"),  # Workstate overview
    # user_app/urls.py
    path("profile/", user_profile, name="profile"),
    path("profile/image/", user_update_image, name="profile-image"),
    path("profile/reset-password/", user_reset_password, name="profile-reset-password"),

    # ======================
    # WORK ITEMS
    # ======================
    path(
        "work-items/",
        user_work_items,
        name="work-items"
    ),

    path(
        "work-items/archived/",
        user_inactive_work_items,
        name="work-items-archived"
    ),

    path(
        "work-items/<int:item_id>/",
        user_work_item_detail,
        name="work-item-detail"
    ),

    path(
        "work-items/<int:item_id>/attachments/",
        user_work_item_attachments,
        name="work-item-attachments"
    ),
    
    path(
        "work-items/<int:item_id>/grouped-links/<str:group_name>/",
        get_grouped_links,
        name="grouped-links"
    ),

    path(
        "attachments/<int:attachment_id>/delete/",
        delete_work_item_attachment,
        name="delete-attachment"
    ),
    path(
        "work-items/<int:item_id>/toggle-archive/",
        toggle_work_item_archive,
        name="work-item-toggle-archive",
    ),

    # ======================
    # DISCUSSIONS (NEW READ RECEIPT SYSTEM)
    # ======================
    
    # Main discussions list page
    path(
        "discussions/",
        user_discussions_list,
        name="discussions-list"
    ),
    
    # Hidden discussions page
    path(
        "discussions/hidden/",
        hidden_discussions_list,
        name="hidden-discussions"
    ),
    
    # Bulk action: Mark all as read
    path(
        "discussions/mark-all-read/",
        user_mark_all_discussions_read,
        name="discussions-mark-all-read"
    ),
    
    # API endpoint: Get discussion statistics
    path(
        "discussions/stats/",
        user_discussion_stats,
        name="discussion-stats"
    ),
    
    # Individual discussion thread (opens in modal/iframe)
    path(
        "discussions/<int:item_id>/",
        user_work_item_discussion,
        name="work-item-discussion"
    ),
    
    # Hide/Unhide discussion
    path(
        "discussions/<int:item_id>/hide/",
        hide_discussion,
        name="hide-discussion"
    ),
    path(
        "discussions/<int:item_id>/unhide/",
        unhide_discussion,
        name="unhide-discussion"
    ),

    # ======================
    # NOTIFICATIONS
    # ======================
    path(
        "notifications/",
        user_notifications,
        name="user-notifications"
    ),
    
    # ======================
    # EMAIL LOGS
    # ======================
    path(
        "email-logs/",
        user_email_logs,
        name="email-logs"
    ),
    path(
        "api/email-logs/<int:email_id>/",
        user_email_detail,
        name="email-detail"
    ),
    
    # ======================
    # REVIEWED FILES
    # ======================
    path(
        "files/accepted/",
        user_accepted_files,
        name="accepted-files"
    ),
    path(
        "files/rejected/",
        user_rejected_files,
        name="rejected-files"
    ),
    
    # ======================
    # DOCUMENTS (SHARED WITH ADMIN - READ-ONLY FOR USERS)
    # ======================
    path(
        "documents/browse/",
        file_manager_view,
        name="file-manager"
    ),
    path(
        "documents/browse/<int:folder_id>/",
        file_manager_view,
        name="file-manager-folder"
    ),
    path(
        "documents/download/<int:attachment_id>/",
        download_file,
        name="download-file"
    ),
    path(
        "documents/download-zip/",
        download_selected_as_zip,
        name="download-zip"
    ),

    
    # File viewer endpoints (shared with admin)
    path("documents/files/preview/<int:attachment_id>/", preview_file, name="preview-file"),
    path("documents/files/info/<int:attachment_id>/", get_file_info, name="file-info"),
    path("documents/files/grouped-links/<int:folder_id>/<str:group_name>/", get_file_manager_grouped_links, name="file-manager-grouped-links"),
    path("documents/files/convert-docx/<int:attachment_id>/", convert_docx_to_html, name="convert-docx"),
    path("documents/files/convert-excel/<int:attachment_id>/", convert_excel_to_html, name="convert-excel"),
    path("documents/files/convert-pptx/<int:attachment_id>/", convert_pptx_to_html, name="convert-pptx"),
]