import os
import re
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string

from accounts.models import WorkItemAttachment, WorkCycle, WorkforcesDepartment
from structure.services.folder_resolution import (
    resolve_folder_context,
    acronym,
)


# =====================================================
# HELPER: WORKCYCLE ACRONYM (YEAR SAFE)
# =====================================================
def workcycle_acronym(title: str) -> str:
    """
    Acronymizes a WorkCycle title while preserving full years.
    """
    if not title:
        return "—"

    parts = []
    for word in title.split():
        if re.fullmatch(r"\d{4}", word):
            parts.append(word)
        else:
            parts.append(acronym(word))

    return " ".join(parts)


def file_exists(attachment):
    """
    Check if the actual file exists in storage.
    """
    if not attachment.file:
        return False
    try:
        return attachment.file.storage.exists(attachment.file.name)
    except Exception:
        return False


def get_file_size(attachment):
    """
    Get file size in human-readable format.
    """
    if not attachment.file:
        return "—"
    try:
        size = attachment.file.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except Exception:
        return "—"


def build_files_list(qs, filters_active):
    """
    Build the files list with validation and filtering.
    Excludes files that no longer exist in storage.
    Includes links (both individual and grouped).
    """
    year = filters_active.get('year')
    attachment_type = filters_active.get('type')
    division = filters_active.get('division')
    section = filters_active.get('section')
    service = filters_active.get('service')
    unit = filters_active.get('unit')
    search = filters_active.get('search', '').strip().lower()

    files = []
    missing_files = []  # Track missing files with details
    
    # Group links by title (similar to file manager)
    from collections import defaultdict
    grouped_links = defaultdict(list)
    regular_items = []

    for attachment in qs:
        # Handle links
        if attachment.is_link():
            if attachment.link_title:
                # Group links by their title
                grouped_links[attachment.link_title].append(attachment)
            else:
                # Links without titles - treat as individual items
                regular_items.append(attachment)
        else:
            # Regular files
            # Skip files that don't exist in storage
            if not file_exists(attachment):
                missing_files.append({
                    'id': attachment.id,
                    'name': attachment.file.name.rsplit("/", 1)[-1] if attachment.file else "Unknown",
                    'uploaded_by': attachment.uploaded_by.get_full_name() if attachment.uploaded_by else "Unknown",
                    'uploaded_at': attachment.uploaded_at,
                })
                continue
            regular_items.append(attachment)
    
    # Process grouped links
    for group_name, links in grouped_links.items():
        # Use the first link for metadata
        first_link = links[0]
        ctx = resolve_folder_context(first_link.folder)
        
        # Safe workcycle resolution
        workcycle = (
            ctx.get("workcycle")
            or getattr(first_link.work_item, "workcycle", None)
        )
        
        # Org filters (post-resolution) - using new simplified structure
        department = ctx.get("department")
        
        # Skip filtering by old organizational structure (deprecated)
        # Only filter by unit (which now maps to department)
        if unit and unit != "N/A":
            if department != unit:
                continue
        
        # Search filter
        if search:
            searchable = f"{group_name} {department or ''}".lower()
            if search not in searchable:
                continue
        
        # Add grouped link entry
        files.append({
            "id": first_link.id,
            "name": group_name,
            "is_link_group": True,
            "link_count": len(links),
            "links": [{"url": link.link_url, "id": link.id} for link in links],
            "type": first_link.get_attachment_type_display(),
            "type_code": first_link.attachment_type,
            "workcycle": workcycle_acronym(workcycle.title) if workcycle else "—",
            "workcycle_id": workcycle.id if workcycle else None,
            "division": "—",  # Deprecated - no longer used
            "section": "—",  # Deprecated - no longer used
            "service": "—",  # Deprecated - no longer used
            "unit": acronym(ctx.get("department")) if ctx.get("department") else "—",
            "uploaded_by": first_link.uploaded_by,
            "uploaded_at": first_link.uploaded_at,
            "reviewed_by": first_link.reviewed_by,
            "reviewed_at": first_link.reviewed_at,
            "accepted_at": first_link.accepted_at,
            "acceptance_status": first_link.acceptance_status,
            "file_size": "—",  # Links don't have file size
        })
    
    # Process regular items (files and individual links)
    for attachment in regular_items:
        ctx = resolve_folder_context(attachment.folder)

        # Safe workcycle resolution
        workcycle = (
            ctx.get("workcycle")
            or getattr(attachment.work_item, "workcycle", None)
        )

        # Org filters (post-resolution) - using new simplified structure
        # Note: division, section, service are deprecated - only department is used now
        department = ctx.get("department")
        
        # Skip filtering by old organizational structure (deprecated)
        # Only filter by unit (which now maps to department)
        if unit and unit != "N/A":
            if department != unit:
                continue

        # Get name based on type
        if attachment.is_link():
            item_name = attachment.link_title or "Link"
            file_url = attachment.link_url
        else:
            item_name = attachment.file.name.rsplit("/", 1)[-1]
            file_url = attachment.file.url
        
        # Search filter
        if search:
            searchable = f"{item_name} {department or ''}".lower()
            if search not in searchable:
                continue

        files.append({
            "id": attachment.id,
            "name": item_name,
            "file_url": file_url,
            "is_link": attachment.is_link(),
            "is_link_group": False,
            "type": attachment.get_attachment_type_display(),
            "type_code": attachment.attachment_type,
            "workcycle": workcycle_acronym(workcycle.title) if workcycle else "—",
            "workcycle_id": workcycle.id if workcycle else None,
            "division": "—",  # Deprecated - no longer used
            "section": "—",  # Deprecated - no longer used
            "service": "—",  # Deprecated - no longer used
            "unit": acronym(department) if department else "—",
            "uploaded_by": attachment.uploaded_by,
            "uploaded_at": attachment.uploaded_at,
            "reviewed_by": attachment.reviewed_by,
            "reviewed_at": attachment.reviewed_at,
            "accepted_at": attachment.accepted_at,
            "acceptance_status": attachment.acceptance_status,
            "file_size": get_file_size(attachment) if not attachment.is_link() else "—",
        })

    return files, missing_files


# =====================================================
# VIEW: ROUTED DOCUMENTS (DEDICATED)
# =====================================================
@login_required
def routed_documents_view(request):
    """
    Dedicated view for routed documents (document tracking files)
    """
    # Determine if user is admin
    is_readonly = not request.user.is_staff
    url_namespace = 'user_app' if is_readonly else 'admin_app'
    base_template = 'user/layout/base.html' if is_readonly else 'admin/layout/base.html'

    # Get routed documents (document tracking specific files)
    from document_tracking.models import Submission
    from structure.models import DocumentFolder
    from django.db.models import Q
    
    # Get all document tracking submissions
    submissions = Submission.objects.all()
    
    # Find all folders related to these submissions
    submission_folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            submission_folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            submission_folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            submission_folder_ids.append(submission.file_manager_folder_id)
    
    # Also find folders that reference these submissions
    related_folders = DocumentFolder.objects.filter(
        Q(primary_submissions__in=submissions) |
        Q(archived_submissions__in=submissions) |
        Q(tracked_submissions__in=submissions)
    ).distinct()
    
    submission_folder_ids.extend([f.id for f in related_folders])
    submission_folder_ids = list(set(submission_folder_ids))  # Remove duplicates
    
    # Get routed documents (attachments from document tracking folders)
    routed_qs = WorkItemAttachment.objects.filter(
        folder_id__in=submission_folder_ids,
        folder__folder_type='attachment'
    ).select_related(
        'uploaded_by', 'folder'
    ).order_by('-uploaded_at')
    
    # Helper function to find submission for attachment
    def find_submission_for_attachment(attachment, submissions_queryset):
        """Helper function to find the submission associated with an attachment"""
        if not attachment.folder:
            return None
        
        folder = attachment.folder
        
        # Check different submission relationships
        for submission in submissions_queryset:
            if (submission.primary_folder_id == folder.id or
                submission.archive_folder_id == folder.id or
                submission.file_manager_folder_id == folder.id):
                return submission
        
        # Check reverse relationships
        if hasattr(folder, 'primary_submissions'):
            for submission in folder.primary_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
                return submission
        
        if hasattr(folder, 'archived_submissions'):
            for submission in folder.archived_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
                return submission
        
        if hasattr(folder, 'tracked_submissions'):
            for submission in folder.tracked_submissions.filter(id__in=submissions_queryset.values_list('id', flat=True)):
                return submission
        
        return None

    # Build routed documents list with submission metadata
    from collections import defaultdict
    routed_grouped_links = defaultdict(list)
    routed_regular_items = []
    
    for attachment in routed_qs:
        if attachment.is_link() and attachment.link_title:
            routed_grouped_links[attachment.link_title].append(attachment)
        else:
            routed_regular_items.append(attachment)
    
    # Build routed documents files list
    routed_documents = []
    
    # Add grouped links
    for group_name, links in routed_grouped_links.items():
        first_link = links[0]
        # Find associated submission
        submission = find_submission_for_attachment(first_link, submissions)
        
        routed_documents.append({
            'id': first_link.id,
            'name': group_name,
            'is_link_group': True,
            'link_count': len(links),
            'links': [{'url': link.link_url, 'id': link.id} for link in links],
            'uploaded_at': first_link.uploaded_at,
            'uploaded_by': first_link.uploaded_by,
            'submission': submission,
            'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
            'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
            'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
            'tracking_number': submission.tracking_number if submission else 'Not assigned'
        })
    
    # Add regular items
    for attachment in routed_regular_items:
        submission = find_submission_for_attachment(attachment, submissions)
        
        if attachment.is_link():
            routed_documents.append({
                'id': attachment.id,
                'name': attachment.link_title or 'Link',
                'file_url': attachment.link_url,
                'is_link': True,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'submission': submission,
                'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
                'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
                'tracking_number': submission.tracking_number if submission else 'Not assigned'
            })
        else:
            routed_documents.append({
                'id': attachment.id,
                'name': attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown',
                'file_url': attachment.file.url if attachment.file else '',
                'is_link': False,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'submission': submission,
                'doc_type': submission.doc_type.name if submission and submission.doc_type else 'No type',
                'status': dict(Submission.STATUS_CHOICES).get(submission.status, submission.status) if submission else 'Unknown',
                'section': submission.assigned_section.name if submission and submission.assigned_section else 'No section',
                'tracking_number': submission.tracking_number if submission else 'Not assigned'
            })

    context = {
        "files": routed_documents,
        "total_files": len(routed_documents),
        "is_readonly": is_readonly,
        "url_namespace": url_namespace,
        "base_template": base_template,
        "view_type": "routed_documents"
    }

    # Handle AJAX requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "admin/page/partials/_routed_documents_content.html",
            context,
            request=request,
        )
        return JsonResponse({
            "status": "success",
            "html": html,
            "total_files": len(routed_documents),
        })

    # Use routed documents template
    return render(request, "admin/page/routed_documents.html", context)


@login_required
def workstate_assets_view(request):
    """
    Dedicated view for workstate assets (non-document tracking files)
    """
    # Determine if user is admin
    is_readonly = not request.user.is_staff
    url_namespace = 'user_app' if is_readonly else 'admin_app'
    base_template = 'user/layout/base.html' if is_readonly else 'admin/layout/base.html'

    # Get document tracking folder IDs to exclude
    from document_tracking.models import Submission
    from structure.models import DocumentFolder
    from django.db.models import Q
    
    submissions = Submission.objects.all()
    submission_folder_ids = []
    for submission in submissions:
        if submission.primary_folder_id:
            submission_folder_ids.append(submission.primary_folder_id)
        if submission.archive_folder_id:
            submission_folder_ids.append(submission.archive_folder_id)
        if submission.file_manager_folder_id:
            submission_folder_ids.append(submission.file_manager_folder_id)
    
    related_folders = DocumentFolder.objects.filter(
        Q(primary_submissions__in=submissions) |
        Q(archived_submissions__in=submissions) |
        Q(tracked_submissions__in=submissions)
    ).distinct()
    
    submission_folder_ids.extend([f.id for f in related_folders])
    submission_folder_ids = list(set(submission_folder_ids))

    # Apply workstate-specific filters
    workstate_year = request.GET.get("workstate_year")
    workstate_attachment_type = request.GET.get("workstate_type")
    workstate_workcycle_id = request.GET.get("workstate_workcycle")
    workstate_search = request.GET.get("workstate_q", "")
    
    # Create workstate queryset (exclude document tracking folders)
    workstate_qs = (
        WorkItemAttachment.objects
        .filter(acceptance_status="accepted")
        .exclude(folder_id__in=submission_folder_ids)  # Exclude document tracking files
        .select_related(
            "uploaded_by",
            "reviewed_by",
            "work_item",
            "work_item__workcycle",
            "folder",
            "folder__workcycle",
        )
        .order_by("-uploaded_at")
    )
    
    if workstate_year:
        workstate_qs = workstate_qs.filter(work_item__workcycle__due_at__year=workstate_year)
    if workstate_attachment_type:
        workstate_qs = workstate_qs.filter(attachment_type=workstate_attachment_type)
    if workstate_workcycle_id:
        workstate_qs = workstate_qs.filter(work_item__workcycle_id=workstate_workcycle_id)
    
    # Build workstate files list
    workstate_files = []
    from collections import defaultdict
    grouped_links = defaultdict(list)
    regular_items = []
    
    for attachment in workstate_qs:
        # Apply search filter
        if workstate_search:
            searchable_text = ""
            if attachment.is_link():
                searchable_text = f"{attachment.link_title or 'Link'} {attachment.work_item.workcycle.title if attachment.work_item and attachment.work_item.workcycle else ''}"
            else:
                filename = attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown'
                searchable_text = f"{filename} {attachment.work_item.workcycle.title if attachment.work_item and attachment.work_item.workcycle else ''}"
            
            if workstate_search.lower() not in searchable_text.lower():
                continue
        
        if attachment.is_link() and attachment.link_title:
            grouped_links[attachment.link_title].append(attachment)
        else:
            regular_items.append(attachment)
    
    # Add grouped links
    for group_name, links in grouped_links.items():
        first_link = links[0]
        workstate_files.append({
            'id': first_link.id,
            'name': group_name,
            'is_link_group': True,
            'link_count': len(links),
            'links': [{'url': link.link_url, 'id': link.id} for link in links],
            'uploaded_at': first_link.uploaded_at,
            'uploaded_by': first_link.uploaded_by,
            'work_item': first_link.work_item,
            'workcycle': first_link.work_item.workcycle if first_link.work_item else None,
            'attachment_type': first_link.attachment_type,
            'attachment_type_display': first_link.get_attachment_type_display(),
        })
    
    # Add regular items
    for attachment in regular_items:
        if attachment.is_link():
            workstate_files.append({
                'id': attachment.id,
                'name': attachment.link_title or 'Link',
                'file_url': attachment.link_url,
                'is_link': True,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'work_item': attachment.work_item,
                'workcycle': attachment.work_item.workcycle if attachment.work_item else None,
                'attachment_type': attachment.attachment_type,
                'attachment_type_display': attachment.get_attachment_type_display(),
            })
        else:
            workstate_files.append({
                'id': attachment.id,
                'name': attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown',
                'file_url': attachment.file.url if attachment.file else '',
                'is_link': False,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'work_item': attachment.work_item,
                'workcycle': attachment.work_item.workcycle if attachment.work_item else None,
                'attachment_type': attachment.attachment_type,
                'attachment_type_display': attachment.get_attachment_type_display(),
            })

    # Filter options
    filters = {
        "years": list(
            WorkCycle.objects
            .values_list("due_at__year", flat=True)
            .distinct()
            .order_by("-due_at__year")
        ),
        "workcycles": list(
            WorkCycle.objects
            .filter(is_active=True)
            .order_by("-due_at")
            .values("id", "title")
        ),
        "attachment_types": WorkItemAttachment.ATTACHMENT_TYPE_CHOICES,
    }

    context = {
        "files": workstate_files,
        "workstate_files": workstate_files,  # Add this for template compatibility
        "total_files": len(workstate_files),
        "total_workstate_files": len(workstate_files),  # Add this for template compatibility
        "workstate_active": {
            "year": workstate_year,
            "type": workstate_attachment_type,
            "workcycle": workstate_workcycle_id,
            "search": workstate_search,
        },
        "filters": filters,
        "is_readonly": is_readonly,
        "url_namespace": url_namespace,
        "base_template": base_template,
        "view_type": "workstate_assets"
    }

    # Handle AJAX requests
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "admin/page/partials/_workstate_assets_content.html",
            context,
            request=request,
        )
        return JsonResponse({
            "status": "success",
            "html": html,
            "total_files": len(workstate_files),
        })

    # Use workstate assets template
    return render(request, "admin/page/workstate_assets.html", context)



# =====================================================
# BULK DOWNLOAD
# =====================================================
@login_required
def bulk_download(request):
    """
    Download multiple files as a ZIP archive.
    Excludes links (non-downloadable items).
    """
    import zipfile
    import io
    from django.http import HttpResponse
    from datetime import datetime
    
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    
    file_ids = request.POST.getlist('file_ids')
    
    if not file_ids:
        return JsonResponse({"status": "error", "message": "No files selected"}, status=400)
    
    # Get attachments (exclude links)
    attachments = WorkItemAttachment.objects.filter(
        id__in=file_ids,
        acceptance_status="accepted"
    ).exclude(
        attachment_type='link'  # Exclude links
    )
    
    if not attachments.exists():
        return JsonResponse({"status": "error", "message": "No downloadable files found"}, status=404)
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for attachment in attachments:
            if not attachment.file:
                continue
            
            try:
                # Check if file exists
                if not file_exists(attachment):
                    continue
                
                # Get file name
                file_name = os.path.basename(attachment.file.name)
                
                # Read file content
                file_content = attachment.file.read()
                
                # Add to ZIP
                zip_file.writestr(file_name, file_content)
            except Exception as e:
                # Skip files that can't be read
                continue
    
    # Prepare response
    zip_buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"files_{timestamp}.zip"
    
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


# =====================================================
# BULK DELETE
# =====================================================
@login_required
@staff_member_required
def bulk_delete_files(request):
    """
    Delete multiple files/links at once.
    Admin only.
    """
    import json
    
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    if not file_ids:
        return JsonResponse({"status": "error", "message": "No items selected"}, status=400)
    
    # Get attachments
    attachments = WorkItemAttachment.objects.filter(
        id__in=file_ids,
        acceptance_status="accepted"
    )
    
    if not attachments.exists():
        return JsonResponse({"status": "error", "message": "No items found"}, status=404)
    
    deleted_count = attachments.count()
    
    # Delete attachments
    attachments.delete()
    
    return JsonResponse({
        "status": "success",
        "message": f"Successfully deleted {deleted_count} item{'s' if deleted_count != 1 else ''}",
        "deleted_count": deleted_count
    })


# =====================================================
# CLEANUP MISSING FILES
# =====================================================
@login_required
@staff_member_required
def cleanup_missing_files(request):
    """
    Delete database records for files that no longer exist in storage.
    Admin only.
    """
    import json
    
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
    
    try:
        data = json.loads(request.body)
        file_ids = data.get('file_ids', [])
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    if not file_ids:
        return JsonResponse({"status": "error", "message": "No items selected"}, status=400)
    
    # Get attachments
    attachments = WorkItemAttachment.objects.filter(
        id__in=file_ids,
        acceptance_status="accepted"
    )
    
    if not attachments.exists():
        return JsonResponse({"status": "error", "message": "No items found"}, status=404)
    
    # Verify these are actually missing files
    cleaned_count = 0
    for attachment in attachments:
        if not attachment.is_link() and not file_exists(attachment):
            attachment.delete()
            cleaned_count += 1
    
    return JsonResponse({
        "status": "success",
        "message": f"Successfully cleaned up {cleaned_count} missing file record{'s' if cleaned_count != 1 else ''}",
        "cleaned_count": cleaned_count
    })


# =====================================================
# WORKSTATE ASSETS API FUNCTIONS
# =====================================================

@login_required
def search_workstate_workcycles(request):
    """
    Search WorkCycles for workstate assets filtering
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    workcycles = WorkCycle.objects.filter(
        title__icontains=query
    ).values('id', 'title').distinct()[:10]
    
    results = []
    for wc in workcycles:
        # Count attachments for this workcycle
        attachment_count = WorkItemAttachment.objects.filter(
            work_item__workcycle_id=wc['id']
        ).count()
        
        results.append({
            'id': wc['id'],
            'title': wc['title'],
            'tracking_number': f"{attachment_count} assets",
            'attachment_count': attachment_count
        })
    
    return JsonResponse({'results': results})


@login_required
def search_workstate_files(request):
    """
    Search files within workstate assets
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in workstate attachments
    attachments = WorkItemAttachment.objects.filter(
        file__icontains=query,
        work_item__isnull=False  # Only workstate assets
    ).select_related('work_item', 'work_item__workcycle').distinct()[:10]
    
    results = []
    seen_workcycles = set()
    
    for attachment in attachments:
        if attachment.work_item and attachment.work_item.workcycle:
            wc = attachment.work_item.workcycle
            if wc.id not in seen_workcycles:
                seen_workcycles.add(wc.id)
                
                file_name = attachment.file.name.rsplit('/', 1)[-1] if attachment.file else 'Unknown'
                
                results.append({
                    'id': wc.id,
                    'title': wc.title,
                    'tracking_number': f"Contains: {file_name}",
                    'file_name': file_name
                })
    
    return JsonResponse({'results': results})


@login_required
def get_workstate_assets(request):
    """
    Get workstate assets with filtering
    """
    workstate_type = request.GET.get('workstate_type')
    workstate_workcycle = request.GET.get('workstate_workcycle')
    
    # Base query for workstate assets
    attachments = WorkItemAttachment.objects.filter(
        work_item__isnull=False
    ).select_related('work_item', 'work_item__workcycle', 'uploaded_by')
    
    # Apply filters
    if workstate_type and workstate_type != '':
        # Filter by workstate type (matrix_a, matrix_b, mov, document, admin_upload)
        if workstate_type == 'matrix_a':
            attachments = attachments.filter(work_item__workcycle__title__icontains='Matrix A')
        elif workstate_type == 'matrix_b':
            attachments = attachments.filter(work_item__workcycle__title__icontains='Matrix B')
        elif workstate_type == 'mov':
            attachments = attachments.filter(work_item__workcycle__title__icontains='MOV')
        elif workstate_type == 'document':
            attachments = attachments.filter(work_item__workcycle__title__icontains='Document')
        elif workstate_type == 'admin_upload':
            attachments = attachments.filter(work_item__workcycle__title__icontains='Admin')
    
    if workstate_workcycle:
        attachments = attachments.filter(work_item__workcycle_id=workstate_workcycle)
    
    # Order by upload date
    attachments = attachments.order_by('-uploaded_at')
    
    # Build files list
    files = []
    for attachment in attachments:
        if attachment.file:
            files.append({
                'id': attachment.id,
                'name': attachment.file.name.rsplit('/', 1)[-1],
                'file_url': attachment.file.url,
                'is_link': False,
                'is_link_group': False,
                'uploaded_at': attachment.uploaded_at,
                'uploaded_by': attachment.uploaded_by,
                'workcycle': attachment.work_item.workcycle.title if attachment.work_item and attachment.work_item.workcycle else 'Unknown'
            })
    
    # Render HTML using workstate assets partial
    context = {
        'files': files,
        'total_files': len(files),
        'is_readonly': False,
    }
    
    html = render_to_string('admin/page/partials/_workstate_assets_content.html', context, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html,
        'total_files': len(files)
    })